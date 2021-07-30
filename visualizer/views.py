

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
ELSEVIER_HEADERS = {'X-ELS-APIKey': settings.SCOPUS_API_KEY}
ELSEVIER_LIMIT = 20

#
# -- Public functions
#


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
    results = []
    start, count = 0, ELSEVIER_LIMIT

    def _serialize_entry(entry):
        """TODO: comment"""
        return {
            'title': entry['dc:title'],
            'first_author': entry['dc:creator'],
            'publication_name': entry['prism:publicationName'],
        }

    # TODO: comment
    while True:
        url = f"{ELSEVIER_BASE_URL}/content/search/scopus?query=ABS({query})&subj={category}&start={start}&count={count}"
        response = requests.get(url, headers=ELSEVIER_HEADERS)
        try:
            response.raise_for_status()
        except:
            print("ERROR: _get_search_results(): response = {response}")

        # Unpack successful response and serialize data
        entries = response.json()['search-results']['entry']
        serialized_entries = list(map(_serialize_entry, entries))

        # Add serialized data to results
        results.extend(serialized_entries)

        # Move on to next page of results
        start += count

        # TEMP
        if start >= 100:
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
