"""
Scopus API wrappers
"""
# Standard
from time import sleep

# 3rd party
from django.conf import settings
from django.db.models import Q, F
import requests

# Internal
from visualizer.models import ScopusClassification, ScopusSource, Search, SearchResult_Category, SearchResult_Entry

# Constants
ELSEVIER_BASE_URL = 'http://api.elsevier.com'
ELSEVIER_HEADERS = {'X-ELS-APIKey': settings.SCOPUS_API_KEY, 'X-ELS-Insttoken': settings.SCOPUS_INST_TOKEN, 'Accept': 'application/json'}
ELSEVIER_PAGE_LIMIT = 100
ELSEVIER_SEARCH_LIMIT = 200 # TODO: put back to 5000
RETRY_LIMIT = 5
RETRY_PAUSE = 30
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
EXCLUDE_DOCTYPES = ['er']  # TODO: Review with Stephen
DOCTYPES = [dt for dt in ALL_DOCTYPES if dt not in EXCLUDE_DOCTYPES]
DOCTYPES_QUERY = ' OR '.join(DOCTYPES)

#
# -- Public functions
#


def get_abstract(scopus_id):
    """TODO: Comment"""
    # Request Scopus abstract
    url = f'{ELSEVIER_BASE_URL}/content/abstract/scopus_id/{scopus_id}'
    response = requests.get(url, headers=ELSEVIER_HEADERS)

    # Unpack abstract text
    try:
        abstract = response.json()['abstracts-retrieval-response']['coredata']['dc:description']['abstract']['ce:para']
    except Exception as exc:
        print(f"get_abstract(): ERROR: {exc}, {url}, {response.json()}")
        raise exc

    return abstract


def get_search_results(query, categories=None, search_id=None):
    """Get search results for query within the specified subject categories.

    !!!
    IMPORTANT: This task is long-running and is designed to be queued for an asynchronous worker.
    !!!

    Example return:
    {
        "CHEM": {                           // category abbreviation
            "1600": {                           // number of query hits for sources with specific classification
                "name": "Chemistry (all)",
                "count": 5,
            },
            "unknown": {                        // number of query hits for sources with unknown classification
                "name": "Unknown",                 
                "count": 3,
            },
            "total": {                          // number of query hits within category
                "name": "Total",                 
                "count": 8,
            },
        },
    }

    Arguments:
    query -- a string; the search query
    categories -- (optional) a list of scopus category abbreviations (e.g. ['MULT','AGRI','CHEM']); when specified, 
        search will be limited to those categories; when unspecified, search will be performed across all categories
    search_id -- (optional) a Search object ID; identifies a Search object that should be used to organize search 
        results; when not provided, a new Search object will be created
    """
    # TODO: Script to cleanup old records and vacuum tables
    # TODO: If fresh search results exist for the specified query and categories, return them immediately

    # Create Search object to link results back to
    if search_id:
        search = Search.objects.get(id=search_id)
    else:
        search = Search.init_search(query, categories) # if categories is None, will be treated as "all categories"

    # TODO: comment, error message
    assert query == search.query, f"Query mismatch, {query}, {search.query}"
    print(f"get_search_results(): INFO: {query}, {search}, {search.context['categories']}, {search.context['finished_categories']}")

    # Assemble list of search categories that are not already finished for the search; this allows
    # us to pick up a search where it left off if it was interrupted.
    search_categories = [c for c in search.context['categories'] if c not in search.context['finished_categories']]

    # TODO: comment
    for category in search_categories:
        _search_category(search, category)

    # TODO: comment
    search.finished = True
    search.save()

    # TODO: Assemble results from data in database for search object
    print(f"get_search_results(): INFO: {query}, assemble results")
    results = {}

    return results

def get_subject_area_classifications():
    """TODO: Comment

    Ref: https://dev.elsevier.com/documentation/SubjectClassificationsAPI.wadl
    """
    categories, classifications = [], []

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
        classifications.append(classification)
        category = classification['abbrev']
        if category not in categories:
            categories.append(category)

    # Sore categories alphabetically
    categories = sorted(categories)

    return (categories, classifications)


#
# -- Private functions
#


def _search_category(search, category):
    """TODO: comment

    Ref: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
    Ref: https://dev.elsevier.com/sc_search_tips.html
    Ref: https://dev.elsevier.com/sc_search_views.html

    Arguments:
    search -- a Search object that search results will be linked back to
    category -- a string; a scopus category abbreviation (e.g. 'CHEM')
    """
    # TODO: comment
    SearchResult_Entry.objects.filter(search=search, category_abbr=category).delete()
    SearchResult_Category.objects.filter(search=search, category_abbr=category).delete()

    # TODO: comment
    sources = ScopusSource.objects.filter(classifications__category_abbr=category)

    # TODO: comment
    last_issn_q = Q()
    if category == search.context['last_category'] and search.context.get('last_issn'):
        last_issn_q = Q(issn__gt=search.context.get('last_issn'))

    # TODO: comment
    p_issns = sources.annotate(issn=F('p_issn')).filter(last_issn_q).exclude(issn__isnull=True).distinct('issn').values('issn')
    e_issns = sources.annotate(issn=F('e_issn')).filter(last_issn_q).exclude(issn__isnull=True).distinct('issn').values('issn')
    issns = p_issns.union(e_issns).order_by('issn')
    issns_count = issns.count()

    # TODO: comment
    for index, issn in enumerate(issns):
        if index % 100 == 0:
            print(f"_search_category(): INFO: {search.query}, {category}, ISSN {index} of {issns_count}")

        # TODO: comment
        _search_category_issn(search, category, issn=issn['issn'])

    # Summarize results with a dictionary of entry counts
    counts = {}
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
    counts['unknown'] = {
        'name': 'Unknown',
        'count': entries.filter(scopus_source__isnull=True).count(),
    }

    # Create search results record for category
    SearchResult_Category.objects.create(
        search=search,
        category_abbr=category,
        counts=counts,
    )

    # TODO: comment
    return counts


def _search_category_issn(search, category, issn):
    """TODO: comment

    Ref: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
    Ref: https://dev.elsevier.com/sc_search_tips.html
    Ref: https://dev.elsevier.com/sc_search_views.html

    Arguments:
    search -- a Search object that search results will be linked back to
    category -- a string; a scopus category abbreviation (e.g. 'CHEM')
    issn -- TODO: comment
    """
    start = 0
    retries = 0

    # Assemble query URL without pagination markers
    # TODO: add doctype limitation to query
    query_url = f'{ELSEVIER_BASE_URL}/content/search/scopus?query=ABS("{search.query}") AND SUBJAREA({category}) AND ISSN({issn})'

    # Paginate through Scopus search results
    while True:
        if start % 1000 == 0:
            print(f"_search_category_issn(): INFO: {search.query}, {category}, {issn}, page {int(start / ELSEVIER_PAGE_LIMIT)}")

        # TODO: comment
        url = f'{query_url}&start={start}&count={ELSEVIER_PAGE_LIMIT}'
        response = requests.get(url, headers=ELSEVIER_HEADERS)
        try:
            response.raise_for_status()
            retries = 0
        except Exception as exc:
            print(f"_search_category_issn(): ERROR: {exc}, {url}, {response.json()}")
            if retries < 5:
                print(f"_search_category_issn(): INFO: will retry in {RETRY_PAUSE} seconds")
                sleep(RETRY_PAUSE)
                retries += 1
                continue
            raise exc

        # Unpack successful response and serialize data
        try:
            # On first pass, confirm there are any results at all
            if start == 0 and response.json()['search-results']['opensearch:totalResults'] in [0,'0']:
                break
            # Confirm there are results for the requested start offset
            entries = response.json()['search-results'].get('entry')
            if not entries:
                break
            # Check for any other errors
            if 'error' in entries[0]:
                raise Exception({entries[0]['error']})
        except Exception as exc:
            print(f"_search_category_issn(): ERROR: {exc}, {url}, {response.json()}")
            raise exc

        # Add result entries to database
        for entry in entries:
            try:
                # Sanity check ISSN
                assert issn in [entry.get('prism:issn'), entry.get('prism:eIssn')], \
                    f"ISSN mismatch, {issn}, {entry.get('prism:issn')}, {entry.get('prism:eIssn')}"

                # Clean scopus ID
                scopus_id = entry['dc:identifier'].replace('SCOPUS_ID:','')

                # Clean DOI
                doi = entry.get('prism:doi') or None
                doi = doi if doi and len(doi) <= DOI_MAX_LENGTH else None

                # Clean document type (subtype)
                subtype = entry['subtype'] or None
                subtype = subtype if subtype and len(subtype) == DOCTYPE_MAX_LENGTH else None

                # Sanity check subtype
                if subtype in EXCLUDE_DOCTYPES:
                    print(f"_search_category_issn(): WARNING: {search.query}, {category}, {issn}, "+
                        f"entry ignored ({subtype}, {scopus_id}, {doi})")

                # Clean first author (creator)
                creator = entry.get('dc:creator') or ''
                creator = creator[:AUTHOR_MAX_LENGTH] if creator else None

                # Create search results record for entry
                SearchResult_Entry.objects.create(
                    search=search,
                    category_abbr=category,
                    scopus_id=scopus_id,
                    doi=doi,
                    title=entry['dc:title'],
                    first_author=creator,
                    document_type=subtype,
                    publication_name=entry['prism:publicationName'],
                    scopus_source=ScopusSource.objects.filter(source_id=entry['source-id']).first(),
                )
            except Exception as exc:
                print(f"_search_category_issn(): ERROR: {exc}, {url}, {entry}")
                raise exc

        # Move on to next page of results
        start += ELSEVIER_PAGE_LIMIT

        # TODO: comment
        if start >= ELSEVIER_SEARCH_LIMIT:
            break

    # Record last category & ISSN searched
    search.context.update({'last_category': category, 'last_issn': issn})
    search.save()
