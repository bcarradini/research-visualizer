

# Standard

# 3rd party
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
import json
import requests

# Internal

# Constants
ELSEVIER_BASE_URL = 'http://api.elsevier.com'
ELSEVIER_HEADERS = {'X-ELS-APIKey': settings.SCOPUS_API_KEY, 'X-ELS-Insttoken': settings.SCOPUS_INST_TOKEN}
ELSEVIER_LIMIT = 20 # TODO: review this

#
# -- Public functions
#


def abstract(request):
    body = json.loads(request.body)
    results = _get_abstract(body['abstract_url'])
    return JsonResponse({'results': results}, status=200)


def search(request):
    body = json.loads(request.body)
    results = _get_search_results(body['query'], body['categories'])
    return JsonResponse({'results': results}, status=200)


def subject_area_classifications(request):
    categories, classifications = _get_subject_area_categories_and_classifications()
    return JsonResponse({'categories': categories, 'classifications': classifications}, status=200)


def index(request):
    return render(request, "index.html", context={})


#
# -- Private functions
#

def _get_abstract(abstract_url):
    """TODO: Comment"""
    print(f"TEMP: _get_abstract(): abstract_url = {abstract_url}")
    response = requests.get(url, headers=ELSEVIER_HEADERS)

    # Convert XML to dictionary
    response_dict = xmltodict.parse(response.content, dict_constructor=dict)

    try:
        abstract = response_dict['abstracts-retrieval-response']['coredata']['dc:description']['abstract']['ce:para']
    except KeyError:
        print("TODO: KeyError")

    return abstract

def _get_search_results(query, categories):
    """TODO: Comment"""
    results = {}

    # TODO: Comment
    for category in categories:
        category_results = _get_search_results_for_category(query, category)

        results[category] = {
            'num_entries': len(category_results),
            'entries': category_results,
        }

    return results

def _get_search_results_for_category(query, category):
    """TODO: comment"""
    print(f"TEMP: _get_search_results_for_category(): category = {category}, query = {query}")
    results = []
    start, count = 0, ELSEVIER_LIMIT

    def _serialize_entry(entry):
        """TODO: comment"""
        try:
            return {
                # TODO: guard against exceptions
                'title': entry['dc:title'],
                'first_author': entry['dc:creator'], # TOOD: sometimes this key is missing
                'publication_name': entry['prism:publicationName'],
                'abstract_url': [link for link in entry['link'] if link['@ref'] == 'self'][0]['@href'],
            }
        except Exception as exc:
            print(f"ERROR: {exc}, {entry}")
            raise exc

    # TODO: comment
    while True:
        url = f'{ELSEVIER_BASE_URL}/content/search/scopus?query=ABS("{query}") AND SUBJAREA({category})&start={start}&count={count}'
        print(f"TEMP: _get_search_results_for_category(): url = {url}")
        response = requests.get(url, headers=ELSEVIER_HEADERS)
        try:
            response.raise_for_status()
        except Exception as exc:
            print(f"ERROR: {exc}, {url}")
            raise exc

        # Unpack successful response and serialize data
        entries = response.json()['search-results']['entry']
        if entries and 'error' in entries[0]:
            return []
        serialized_entries = list(map(_serialize_entry, entries))

        # Add serialized data to results
        results.extend(serialized_entries)

        # Move on to next page of results
        start += count

        # TEMP
        break
        # TEMP

    return results

def _get_subject_area_categories_and_classifications():
    """TODO: Comment"""
    # Request Scopus subject area classifications
    url = f"{ELSEVIER_BASE_URL}/content/subject/scopus"
    response = requests.get(url, headers=ELSEVIER_HEADERS)
    response.raise_for_status()

    # Unpack successful response
    classifications = response.json()['subject-classifications']['subject-classification']
    categories = sorted(list(set(map(lambda c: c['abbrev'], classifications))))

    return (categories, classifications)
