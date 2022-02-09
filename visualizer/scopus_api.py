"""
TODO: comment
"""

# 3rd party
from django.conf import settings
import requests

# Internal
from visualizer.models import ScopusSource

# Constants
ELSEVIER_BASE_URL = 'http://api.elsevier.com'
ELSEVIER_HEADERS = {'X-ELS-APIKey': settings.SCOPUS_API_KEY, 'X-ELS-Insttoken': settings.SCOPUS_INST_TOKEN, 'Accept': 'application/json'}
ELSEVIER_LIMIT = 20 # TODO: review this

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
        print(f"ERROR: {exc}, {entry}")
        raise exc

    return abstract

def get_search_results(query, categories):
    """TODO: Comment"""
    results = {}

    # TODO: Comment
    for category in categories:
        category_results = get_search_results_for_category(query, category)

        results[category] = {
            'num_entries': len(category_results),
            'entries': category_results,
        }

    return results

def get_search_results_for_category(query, category):
    """TODO: comment

    Document Type (search results -> entry -> `subtype`):



    # Ref: https://dev.elsevier.com/sc_search_tips.html
    # Ref: https://dev.elsevier.com/sc_search_views.html

    """
    print(f"TEMP: get_search_results_for_category(): category = {category}, query = {query}")
    results = []
    start, count = 0, ELSEVIER_LIMIT
    sources = {}

    def _serialize_entry(entry):
        # TODO: comment
        try:
            serialized_entry = {
                # TODO: guard against exceptions
                'title': entry['dc:title'], # TOOD: sometimes this key is missing
                'first_author': entry['dc:creator'], # TOOD: sometimes this key is missing
                'publication_name': entry['prism:publicationName'],
                'scopus_id': entry['dc:identifier'].replace('SCOPUS_ID:',''),
                'doi': entry['prism:doi'],
                'source_id': entry['source-id'],
                # 'abstract_url': [link for link in entry['link'] if link['@ref'] == 'self'][0]['@href'],
            }
        except Exception as exc:
            print(f"ERROR: {exc}, {entry}")
            return None

        # TODO: comment
        try:
            source = ScopusSource.objects.get(source_id=serialized_entry['source_id'])
        except ScopusSource.DoesNotExist as exc:
            print(f"ERROR: {exc}, {entry}")
            source = None

        # TODO: comment
        if source:
            classifications = source.classifications.all()
            serialized_entry['classifications'] = list(source.classifications.values('category_abbr','code','name'))

        return serialized_entry

    # TODO: comment
    while True:
        url = f'{ELSEVIER_BASE_URL}/content/search/scopus?query=ABS("{query}") AND SUBJAREA({category}) AND DOCTYPE({DOCTYPES_QUERY})&start={start}&count={count}'
        response = requests.get(url, headers=ELSEVIER_HEADERS)
        try:
            response.raise_for_status()
        except Exception as exc:
            print(f"ERROR: {exc}, {url}")
            raise exc

        # Unpack successful response and serialize data
        try:
            entries = response.json()['search-results']['entry']
            if entries and 'error' in entries[0]:
                return []
        except Exception as exc:
            print(f"ERROR: {exc}, {url}")
            return results


        # Add serialized data to results
        results.extend(list(map(_serialize_entry, entries)))

        # Move on to next page of results
        start += count

        # TEMP
        import random
        if random.randint(0,1) == 0:
            break
        # TEMP

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
        # sc will be formatted like:
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
