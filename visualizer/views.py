"""
Views to support Visualizer URLs
"""
# 3rd party
from django.http import JsonResponse
from django.shortcuts import render
import json

# Internal
from project.worker import queue_job
from visualizer.models import Search
from visualizer.scopus_api import get_abstract, get_search_results, get_subject_area_classifications


#
# -- Public functions
#


def abstract(request, scopus_id):
    results = get_abstract(scopus_id)
    return JsonResponse({'results': results}, status=200)


def search(request):
    # Unpack request body
    body = json.loads(request.body)
    # Launch asynchronous search
    job_id, search_id = _search(body['query'], body['categories'])
    # Respond with job ID
    return JsonResponse({'job': {'id': job_id, 'search_id': search_id}}, status=200)


def subject_area_classifications(request):
    categories, classifications = get_subject_area_classifications()
    return JsonResponse({'categories': categories, 'classifications': classifications}, status=200)


def index(request):
    return render(request, "index.html", context={})


#
# -- Private functions
#


def _search(query, categories):
    """Perform query-based search, scoped by the provided list of categories.

    Arguments:
    query -- a string; the search query
    categories -- a list of strings; scopus category abbreviations (e.g. ['MULT','AGRI','CHEM'])
    """
    search = Search._init_search(query, categories)
    job = queue_job(get_search_results, args=(query, categories, search.id), job_timeout=12*60*60)
    return (job.id, search.id)
