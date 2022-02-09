

# 3rd party
from django.http import JsonResponse
from django.shortcuts import render
import json

# Internal
from visualizer.scopus_api import get_abstract, get_search_results, get_subject_area_classifications

#
# -- Public functions
#


def abstract(request, scopus_id):
    results = get_abstract(scopus_id)
    return JsonResponse({'results': results}, status=200)


def search(request):
    body = json.loads(request.body)
    results = get_search_results(body['query'], body['categories'])
    return JsonResponse({'results': results}, status=200)


def subject_area_classifications(request):
    categories, classifications = get_subject_area_classifications()
    return JsonResponse({'categories': categories, 'classifications': classifications}, status=200)


def index(request):
    return render(request, "index.html", context={})


#
# -- Private functions
#

