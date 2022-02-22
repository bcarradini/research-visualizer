"""
TODO: comment
"""

# 3rd party
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
import requests

# Internal
from visualizer.models import ScopusClassification, ScopusSource, Search, SearchResult_Category, SearchResult_Entry

# Constants
ELSEVIER_BASE_URL = 'http://api.elsevier.com'
ELSEVIER_HEADERS = {'X-ELS-APIKey': settings.SCOPUS_API_KEY, 'X-ELS-Insttoken': settings.SCOPUS_INST_TOKEN, 'Accept': 'application/json'}
ELSEVIER_LIMIT = 100
STALE_RESULTS_HRS = 24
AUTHOR_MAX_LENGTH = SearchResult_Entry._meta.get_field('first_author').max_length
DOCTYPE_MAX_LENGTH = SearchResult_Entry._meta.get_field('document_type').max_length
DOI_MAX_LENGTH = SearchResult_Entry._meta.get_field('doi').max_length

# Scopus Document Types (search results -> entry -> `subtype`)
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
        print(f"get_abstract(): ERROR: {exc}, {entry}")
        raise exc

    return abstract


def get_search_results(query, categories, search_id=None):
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
    categories -- a list of strings; scopus category abbreviations (e.g. ['MULT','AGRI','CHEM'])
    search_id -- (optional) a Search object ID; identifies a Search object that should be used to
        organize search results; when not provided, a new Search object will be created
    """
    results = {}

    # TODO: Script to cleanup old records and vacuum tables
    # TODO: If fresh search results exist for the specified query and categories, return them immediately

    # Create Search object to link results back to
    if search_id:
        search = Search.objects.get(id=search_id)
    else:
        search = Search._init_search(query, categories)

    # TODO: comment, error message
    assert query == search.query, f"Query mismatch, {query}, {search.query}"

    # Assemble list of search categories that are not already finished for the search; this allows
    # us to pick up a search where it left off if it was interrupted.
    search_categories = [c for c in categories if c not in search.context['finished_categories']]
    print(f"get_search_results(): INFO: {query}, {search_categories}")

    # TODO: comment
    for category in search_categories:
        results[category] = _get_category_search_results(search, category)
        search.context['finished_categories'].append(category)
        search.save()

    search.finished = True
    saerch.save()

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


def _get_category_search_results(search, category):
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

    # TODO: comment
    sources = ScopusSource.objects.filter(classifications__category_abbr=category).exclude(Q(p_issn__isnull=True) & Q(e_issn__isnull=True))
    issns = sources.distinct('p_issn', 'e_issn').values_list('p_issn', 'e_issn')
    issns_count = issns.count()

    # TODO: comment
    for index, (p_issn, e_issn) in enumerate(issns):
        if index % 100 == 0:
            print(f"_get_category_search_results(): INFO: {search.query}, {category}, source {index} of {issns_count}")

        # TODO: comment
        _category_issn_search(search, category, p_issn=p_issn, e_issn=e_issn)

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


def _category_issn_search(search, category, p_issn=None, e_issn=None):
    """TODO: comment

    Ref: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
    Ref: https://dev.elsevier.com/sc_search_tips.html
    Ref: https://dev.elsevier.com/sc_search_views.html

    Arguments:
    search -- a Search object that search results will be linked back to
    category -- a string; a scopus category abbreviation (e.g. 'CHEM')
    p_issn -- TODO
    e_issn -- TODO
    """
    assert p_issn or e_issn, f"ISSN missing"
    start, count = 0, ELSEVIER_LIMIT
    issns = list(filter(lambda issn: bool(issn), [p_issn, e_issn]))

    # Assemble query URL without pagination markers
    # TODO: add doctype limitation to query
    # TODO: Verify that ISSN query formulation is correct
    issn_subquery = ' OR '.join(issns)
    query = f'ABS("{search.query}") AND SUBJAREA({category}) AND ISSN({issn_subquery})'
    query_url = f'{ELSEVIER_BASE_URL}/content/search/scopus?query={query}'

    # Paginate through Scopus search results
    while True:
        if start % 1000 == 0:
            print(f"_category_issn_search(): INFO: {search.query}, {category}, {query}, page {int(start / ELSEVIER_LIMIT)}")

        # TODO: comment
        url = f'{query_url}&start={start}&count={count}'
        response = requests.get(url, headers=ELSEVIER_HEADERS)
        try:
            response.raise_for_status()
        except Exception as exc:
            print(f"_category_issn_search(): ERROR: {exc}, {url}, {response.json()}")
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
            print(f"_category_issn_search(): ERROR: {exc}, {url}, {response.json()}")
            raise exc

        # Add result entries to database
        for entry in entries:
            try:
                # Sanity check ISSN
                assert (entry.get('prism:issn') in issns) or (entry.get('prism:eIssn') in issns), \
                    f"ISSN mismatch, {entry.get('prism:issn')}, {entry.get('prism:eIssn')}, {issns}"

                # Clean scopus ID
                scopus_id = entry['dc:identifier'].replace('SCOPUS_ID:','')

                # Clean DOI
                doi = entry.get('prism:doi') or None
                doi = doi if len(doi) <= DOI_MAX_LENGTH else None

                # Clean document type (subtype)
                subtype = entry['subtype'] or ''
                subtype = subtype if len(subtype) == DOCTYPE_MAX_LENGTH else None

                # Sanity check subtype
                if subtype in EXCLUDE_DOCTYPES:
                    print(f"_category_issn_search(): WARNING: {search.query}, {category}, entry ignored ({subtype}, {scopus_id}, {doi})")

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
                print(f"_category_issn_search(): ERROR: {exc}, {url}, {entry}")
                raise exc

        # Move on to next page of results
        start += count

        # TODO: comment
        if start >= 5000:
            break
