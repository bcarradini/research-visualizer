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
ELSEVIER_LIMIT = 100 # TODO: review this
STALE_RESULTS_HRS = 1 # TODO: set to 24 after testing

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
DOCTYPES = ['ar', 'bk', 'cp'] # TODO: Review with Stephen
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
    """TODO: Comment

    IMPORTANT: This task is long-running and is designed to be queued for an asynchronous worker.

    Arguments:
    query -- a string; the search query
    categories -- a list of strings; scopus category abbreviations (e.g. ['MULT','AGRI','CHEM'])
    search_id -- (optional) a Search object ID; identifies a Search object that should be used to
        organize search results; when not provided, a new Search object will be created
    """
    results = {}

    # Delete stale search results
    searches_cutoff = timezone.now()-timezone.timedelta(hours=STALE_RESULTS_HRS)
    searches = Search.objects.exclude(id=search_id).filter(created__lt=searches_cutoff)
    for search in searches:
        # Delete search object
        search.delete()

    # If fresh search results exist for the specified query and categories, return them immediately
    # TODO: confirm scopus search is case-insensitive; it should be
    # searches = Search.objects.filter(query__iexact=query)

    # Create Search object to link results back to
    if search_id:
        search = Search.objects.get(id=search_id)
    else:
        search = Search.objects.create(query=query, context={'categories': categories, 'finished_categories': []})

    # TODO: Comment
    for category in categories:
        results[category] = _get_category_search_results(search, query, category)
        search.context['finished_categories'].append()

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


def _get_category_search_results(search, query, category):
    """TODO: comment

    Ref: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
    Ref: https://dev.elsevier.com/sc_search_tips.html
    Ref: https://dev.elsevier.com/sc_search_views.html

    Arguments:
    search -- a Search object that search results will be linked back to
    query -- a string; the search query
    category -- a string; a scopus category abbreviation (e.g. 'CHEM')
    """
    # TODO: comment
    sources = ScopusSource.objects.filter(classifications__category_abbr=category).exclude(Q(p_issn__isnull=True) & Q(e_issn__isnull=True))
    issns = sources.distinct('p_issn', 'e_issn').values_list('p_issn', 'e_issn')
    for p_issn, e_issn in issns:
        _category_issn_search(search, query, category, p_issn=p_issn, e_issn=e_issn)

    # Summarize results with a dictionary of entry counts
    counts = {}
    entries = SearchResult_Entry.objects.filter(search=search, category_abbr=category)

    # Get entry count for category as a whole
    counts['total']: {
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
    counts['unknown']: {
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


def _category_issn_search(search, query, category, p_issn=None, e_issn=None):
    """TODO: comment

    Ref: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
    Ref: https://dev.elsevier.com/sc_search_tips.html
    Ref: https://dev.elsevier.com/sc_search_views.html

    Arguments:
    search -- a Search object that search results will be linked back to
    query -- a string; the search query
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
    query = f'ABS("{query}") AND SUBJAREA({category}) AND ISSN({issn_subquery})'
    query_url = f'{ELSEVIER_BASE_URL}/content/search/scopus?query={query}'

    # Paginate through Scopus search results
    while True:
        if start % 500 == 0:
            print(f"_category_issn_search(): INFO: {category}, {issns}, '{query}', page {int(start / ELSEVIER_LIMIT)}")

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
                # Get source ID and name from entry
                assert (p_issn == entry.get('prism:issn')) or (e_issn == entry.get('prism:eIssn')), \
                    f"ISSN mismatch, {p_issn} -> {entry.get('prism:issn')}, {e_issn} -> {entry.get('prism:eIssn')}"

                # Create search results record for entry
                SearchResult_Entry.objects.create(
                    search=search,
                    category_abbr=category,
                    scopus_id=entry['dc:identifier'].replace('SCOPUS_ID:',''),
                    title=entry['dc:title'],
                    first_author=entry.get('dc:creator'), # TODO: Sometimes this is missing
                    document_type=entry['subtype'],
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
