"""
Scopus API wrappers
"""
# Standard
from collections import OrderedDict
from datetime import datetime
from time import sleep
from urllib.parse import quote_plus

# 3rd party
from django.conf import settings
from django.db import IntegrityError
import requests

# Internal
from visualizer.models import (
    Search,
    SearchResult_Category,
    SearchResult_Entry,
    ScopusClassification,
    ScopusSource,
    CATEGORIES,
    FINISHED_CATEGORIES,
    NEXT_CATEGORY,
    NEXT_CURSOR,
)

# Constants
ELSEVIER_BASE_URL = 'http://api.elsevier.com'
ELSEVIER_HEADERS = {'X-ELS-APIKey': settings.SCOPUS_API_KEY, 'X-ELS-Insttoken': settings.SCOPUS_INST_TOKEN, 'Accept': 'application/json'}
ELSEVIER_PAGE_LIMIT = 200 # https://dev.elsevier.com/api_key_settings.html
ELSEVIER_FIRST_CURSOR = '*'
RETRY_PAUSE = 60
STALE_RESULTS_HRS = 24
AUTHOR_MAX_LENGTH = SearchResult_Entry._meta.get_field('first_author').max_length
DOCTYPE_MAX_LENGTH = SearchResult_Entry._meta.get_field('document_type').max_length
DOI_MAX_LENGTH = SearchResult_Entry._meta.get_field('doi').max_length

# Scopus Document Types
# ar - Article
# ab - Abstract Report
# bk - Book
# bz - Business Article
# ch - Book Chapter
# cp - Conference Paper
# cr - Conference Review
# ed - Editorial
# er - Erratum
# le - Letter
# no - Note
# pr - Press Release
# re - Review
# sh - Short Survey
ALL_DOCTYPES = ['ar', 'ab', 'bk', 'bz', 'ch', 'cp', 'cr', 'ed', 'er', 'le', 'no', 'pr', 're', 'sh']
EXCLUDE_DOCTYPES = ['bk', 'ch', 'ed', 'er', 'le', 'no', 'pr', 're', 'sh']
DOCTYPES = [dt for dt in ALL_DOCTYPES if dt not in EXCLUDE_DOCTYPES]
DOCTYPES_QUERY = ' OR '.join(DOCTYPES)

#
# -- Public functions
#


def get_abstract(scopus_id):
    """Get abstract for document identified by Scopus ID.

    Arguments:
    scopus_id -- a Scopus ID
    """
    # Request Scopus abstract
    url = f'{ELSEVIER_BASE_URL}/content/abstract/scopus_id/{scopus_id}'
    response = requests.get(url, headers=ELSEVIER_HEADERS)

    # Unpack abstract text
    try:
        description = response.json()['abstracts-retrieval-response']['coredata']['dc:description']
        if isinstance(description, str):
            abstract = description
        else:
            abstract = description['abstract']['ce:para']
    except Exception as exc:
        print(f"get_abstract(): ERROR: {exc}, {url}, {response.json()}")
        raise exc

    return abstract


def get_search_results(query, categories=None, search_id=None):
    """Return dictionary of search results for query within the specified subject area categories.

    !!!
    IMPORTANT: This task is long-running and is designed to be queued for an asynchronous worker.
    !!!

    Notes:
    - Search will be performed against abstracts in the Scopus database
    - Search uses a "loose or approximate phrase" approach, meaning that multi-word queries are
        treated as whole phrases but that punctuation/pluralization are ignored. For example,
        if the query is "social media", documents that contain only "social" or "media" will be
        excluded but documents containing "social-media" or "social medias" will be included.
    - Search supports a limited number of boolean operators (see BOOLEAN_OPERATORS constant).
    - Search is case-insensitive with regard to query terms but case-sensitive with regard to boolean
        operators embedded in the query string. In other words, lowercase "and" will be treated
        as a query term but uppercase "AND" will be treated as a boolean operator.

    Arguments:
    query -- a string; the search query
    categories -- (optional) a list of scopus category abbreviations (e.g. ['MULT','AGRI','CHEM']);
        when specified, search will be limited to those categories; when unspecified, search will
        be performed across all categories
    search_id -- (optional) a Search object ID; identifies a Search object that should be used to
        organize search results; when not provided, a new Search object will be created
    """
    # Create Search object to link results back to
    if search_id:
        search = Search.objects.get(id=search_id)
        assert query == search.query, f"Query mismatch, {query}, {search.query}"
    else:
        search = Search.init_search(query, categories)

    # Log what's about to happen
    search_categories = search.context[CATEGORIES]
    finished_categories = search.context[FINISHED_CATEGORIES]
    print(f"get_search_results(): INFO: {query}, {search}, {search_categories}, {finished_categories}")

    # Assemble list of categories that are not already finished (i.e. still need to be searched);
    # this allows us to pick up an interrupted search where it left off.
    unfinished_categories = [c for c in search_categories if c not in finished_categories]

    # Generate search results for each category; results are stored in the database, not returned
    for category in unfinished_categories:
        _search_category(search, category)

    # Assemble results from database for search
    results = {}
    for category in search_categories:
        category_results = SearchResult_Category.objects.filter(search=search, category_abbr=category).first()
        if category_results:
            results[category] = category_results.counts
        else:
            results[category] = None

    return results


def get_subject_area_classifications():
    """Return dictionary of Scopus subject area classifications (and parent categories).

    References:
    https://dev.elsevier.com/documentation/SubjectClassificationsAPI.wadl
    """
    categories, classifications = {}, {}

    # Request Scopus subject area classifications
    url = f"{ELSEVIER_BASE_URL}/content/subject/scopus"
    response = requests.get(url, headers=ELSEVIER_HEADERS)
    response.raise_for_status()

    # Unpack successful response
    subject_classifications = response.json()['subject-classifications']['subject-classification']
    for classification in subject_classifications:
        # classification will be formatted like:
        # {
        #     "abbrev":"AGRI",    // The "category" in our vernacular
        #     "code":"1101",      // The "classification" in our vernacular
        #     "description":"Agricultural and Biological Sciences",
        #     "detail":"Agricultural and Biological Sciences (miscellaneous)"
        # }
        category = classification['abbrev']
        classifications[classification['code']] = {
            'code': classification['code'],
            'name': classification['detail'],
            'category_abbr': category,
            'category_name': classification['description'],
        }
        if category not in categories:
            categories[category] = {
                'abbr': category,
                'name': classification['description'],
            }

    return (categories, classifications)


#
# -- Private functions
#


def _search_category(search, category):
    """Perform Scopus search within subject area category; store summarized category results in the database.

    Arguments:
    search -- a Search object that defines the parameters of the search
    category -- a string; a scopus category abbreviation (e.g. 'CHEM')
    """
    # Generate search result entries in database
    _search_category_entries(search, category)

    # Summarize results with a dictionary of entry counts
    counts = OrderedDict({})
    entries = SearchResult_Entry.objects.filter(search=search, category_abbr=category)

    # Get entry count for category as a whole
    counts['total'] = {
        'name': 'Total',
        'count': entries.count(),
    }

    # Get entry counts for each classification
    for classification in ScopusClassification.objects.filter(category_abbr=category):
        counts[classification.code] = {
            'name': classification.name,
            'count': entries.filter(scopus_source__classifications__code=classification.code).count(),
        }

    # Get entry count for unknown classification
    counts[ScopusClassification.UNKNOWN] = {
        'name': 'Unknown',
        'count': entries.filter(scopus_source__isnull=True).count(),
    }

    # Create search results record for category
    SearchResult_Category.objects.update_or_create(
        search=search,
        category_abbr=category,
        defaults={'counts': counts}
    )

    # Mark the category as finished
    search.context[FINISHED_CATEGORIES].append(category)
    search.save()


def _search_category_entries(search, category):
    """Perform Scopus search within subject area category; store result entries in the database.

    References:
    https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
    https://dev.elsevier.com/sc_search_tips.html
    https://dev.elsevier.com/sc_search_views.html
    https://dev.elsevier.com/api_key_settings.html

    Arguments:
    search -- a Search object that defines the parameters of the search
    category -- a string; a scopus category abbreviation (e.g. 'CHEM')
    """
    page = 0
    page_cursor = ELSEVIER_FIRST_CURSOR
    retry = True

    # If search of this category was previously interrupted, try to pick up where we left off
    if category == search.context[NEXT_CATEGORY] and search.context[NEXT_CURSOR]:
        page_cursor = search.context[NEXT_CURSOR]

    # Log start
    print(f"_search_category_entries(): INFO: {search.query}, {category}, cursor {page_cursor}")

    # Assemble query URL without pagination markers
    query_url = f'{ELSEVIER_BASE_URL}/content/search/scopus?query=ABS({search.scopus_query}) AND SUBJAREA({category}) AND DOCTYPE({DOCTYPES_QUERY})'

    #
    # -- Paginate through Scopus search results
    #

    while True:
        # Add pagination markers to query URL before performing GET request. Use cursor pagination to
        # "execute deep pagination searching," so as to not be cut off at 5000 results
        url = f'{query_url}&cursor={page_cursor}&count={ELSEVIER_PAGE_LIMIT}'
        response = requests.get(url, headers=ELSEVIER_HEADERS)
        try:
            response.raise_for_status()
        except Exception as exc:
            print(f"_search_category_entries(): ERROR: {exc}, {url}, {response.headers}, {response.json()}")

            # If we've exceeded our quota (429 TOO MANY REQUESTS), log reset timestamp before raising exception
            if response.status_code == 429:
                quota_reset = response.headers.get('X-RateLimit-Reset')
                if quota_reset:
                    print(f"_search_category_entries(): INFO: Quota will reset at {datetime.fromtimestamp(int(quota_reset))}")
                raise exc

            # Otherwise, retry once before raising exception
            if retry:
                print(f"_search_category_issn(): INFO: Will retry in {RETRY_PAUSE} seconds")
                sleep(RETRY_PAUSE)
                retry = False
                continue

            raise exc

        # Unpack successful response
        try:
            search_results = response.json()['search-results']

            # Log status every 5 pages
            if page % 5 == 0:
                quota = response.headers.get('X-RateLimit-Remaining')
                total = search_results.get('opensearch:totalResults')
                print(f"_search_category_entries(): INFO: {search.query}, {category}, {total} results, page {page}, ({quota} HTTP request quota remaining)")

            # If there are no results for the requested page, end pagination
            entries = search_results.get('entry')
            if not entries:
                print(f"_search_category_entries(): INFO: {search.query}, {category}, page {page}, no entries, end pagination")
                break

            # Check for any other errors
            if 'error' in entries[0]:
                if 'set was empty' in entries[0]['error']:
                    print(f"_search_category_entries(): INFO: {search.query}, {category}, page {page}, no entries, end pagination")
                    break
                else:
                    raise Exception(entries[0]['error'])
        except Exception as exc:
            print(f"_search_category_entries(): ERROR: {exc}, {url}, {response.headers}, {response.json().keys()}")
            raise exc

        # Create an internal search result entry for each Scopus result entry
        for entry in entries:
            _create_search_result_entry(search, category, url, entry)

        # Get next page cursor; set next cursor on search object; increment page counter
        try:
            page_cursor = quote_plus(search_results['cursor']['@next'])
            search.set_next_cursor(category, page_cursor)
            page += 1
        except Exception as exc:
            print(f"_search_category_entries(): ERROR: {exc}, {url}, {response.headers}, {response.json()}")
            raise exc


def _create_search_result_entry(search, category, url, entry):
    """Create an internal search result entry for Scopus search result entry.

    References:
    https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
    https://dev.elsevier.com/sc_search_views.html

    Arguments:
    search -- a Search object that defines the parameters of the search
    category -- a string; a scopus category abbreviation (e.g. 'CHEM')
    entry -- a Scopus result entry retrieved via the Scopus search API
    url -- the Scopus search URL used to fetch the entry
    """
    try:
        # Clean scopus ID
        scopus_id = entry['dc:identifier'].replace('SCOPUS_ID:','')

        # Clean DOI
        doi = entry.get('prism:doi') or None
        doi = doi if doi and len(doi) <= DOI_MAX_LENGTH else None

        # Clean document type (subtype)
        subtype = entry.get('subtype') or None
        subtype = subtype if subtype and len(subtype) == DOCTYPE_MAX_LENGTH else None

        # Sanity check subtype
        if subtype in EXCLUDE_DOCTYPES:
            print(f"_create_search_result_entry(): WARNING: {search.query}, {category}, "+
                f"entry ignored ({scopus_id}, {doi}, {subtype})")
            return

        # Clean first author (creator)
        creator = entry.get('dc:creator') or ''
        creator = creator[:AUTHOR_MAX_LENGTH] if creator else None

        # Create database record for entry
        try:
            SearchResult_Entry.objects.create(
                search=search,
                category_abbr=category,
                scopus_id=scopus_id,
                doi=doi,
                title=entry['dc:title'],
                first_author=creator,
                document_type=subtype,
                publication_name=entry.get('prism:publicationName'),
                scopus_source=ScopusSource.objects.filter(source_id=entry['source-id']).first(),
            )
        except (IntegrityError, KeyError):
            # 1. We get here if the creation attempt violates the following unique constraint:
            #      unique_together = [('search', 'category_abbr', 'scopus_id')]
            #    We ignore this error because the document has already been recorded in the
            #    search results for this category. Let's get on with life.
            # 2. We get here if dc:title or source-id are missing; skip entry
            pass

    except Exception as exc:
        print(f"_create_search_result_entry(): ERROR: {exc}, {url}, {entry}")
        raise exc
