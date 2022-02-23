"""
Views to support Visualizer URLs
"""
# Standard
import json

# 3rd party
from django.http import JsonResponse
from django.shortcuts import render

# Internal
from project.worker import queue_job
from visualizer.models import Search
from visualizer.scopus import get_abstract, get_search_results, get_subject_area_classifications


#
# -- Public functions
#


def abstract(request, scopus_id):
    """Get abstract for document identified by Scopus ID.

    Arguments:
    request -- an HttpRequest object
    scopus_id -- a Scopus ID
    """
    results = get_abstract(scopus_id)
    return JsonResponse({'results': results}, status=200)


def search(request):
    """Get Scopus search results for query across specified subject categories.

    Notes:
    - Search will be performed against abstracts in the Scopus database
    - Search uses a "loose or approximate phrase" approach, meaning that multi-word queries are
        treated as whole phrases but that punctuation/pluralization are ignored. For example,
        if the query is "social media", documents that contain only "social" or "media" will be
        excluded but documents containing "social-media" or "social medias" will be included.

    Arguments:
    request -- an HttpRequest object with request body that contains:
        query -- a string
        categories -- (optional) a list of scopus category abbreviations (e.g. ['AGRI','CHEM']);
            when specified, search will be limited to those categories; when unspecified, search
            will be performed across all categories
    """
    # Unpack request body
    body = json.loads(request.body)
    # Launch asynchronous search
    job_id, search_id = _search(body['query'], body.get('categories'))
    # Respond with job ID
    return JsonResponse({'job': {'id': job_id, 'search_id': search_id}}, status=200)


def subject_area_classifications(request):
    """Get Scopus subject area classifications (and parent categories)."""
    categories, classifications = get_subject_area_classifications()
    return JsonResponse({'categories': categories, 'classifications': classifications}, status=200)


def index(request):
    """Returned rendered index template."""
    return render(request, "index.html", context={})


#
# -- Private functions
#


def _search(query, categories=None):
    """Perform query-based search, scoped by the provided list of categories.

    Arguments:
    query -- a string; the search query
    categories -- (optional) a list of scopus category abbreviations (e.g. ['AGRI','CHEM']);
        when specified, search will be limited to those categories; when unspecified, search
        will be performed across all categories
    """
    search_obj = Search.init_search(query, categories)
    job = queue_job(get_search_results, args=(query, categories, search_obj.id), job_timeout=12*60*60)
    return (job.id, search_obj.id)
