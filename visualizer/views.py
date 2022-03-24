"""
Views to support Visualizer URLs
"""
# Standard
import json

# 3rd party
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

# Internal
from project.worker import queue_job
from visualizer.models import (
    ScopusClassification,
    Search,
    SearchResult_Entry,
    CATEGORIES,
    FINISHED_CATEGORIES,
)
from visualizer.scopus import get_abstract, get_search_results, get_subject_area_classifications

# Constants
MAX_LIMIT = 100

#
# -- Public functions
#


@require_GET
def abstract(request, scopus_id):
    """Get abstract for document identified by Scopus ID.

    Arguments:
    request -- an HttpRequest object
    scopus_id -- a Scopus ID
    """
    results = get_abstract(scopus_id)
    return JsonResponse({'results': results}, status=200)


@require_POST
def search(request):
    """Get Scopus search results for query across specified subject area categories.

    Arguments:
    request -- an HttpRequest object with request body that contains:
        query -- a string
        categories -- (optional) a list of scopus category abbreviations (e.g. ['AGRI','CHEM']);
            when specified, search will be limited to those categories; when unspecified, search
            will be performed across all categories.
    """
    # Unpack request body
    body = json.loads(request.body)

    # Launch asynchronous search
    job_id, search_id = _search(body['query'], body.get('categories'))

    # Respond with job ID and search ID
    return JsonResponse({'job': {'id': job_id, 'search_id': search_id}}, status=200)


@require_GET
def search_results(request, search_id=None):
    """TODO: comments"""
    response = {}

    # TODO: comment
    if search_id:
        search = _get_search(search_id) # will raise if search is not found
        response = {
            'results': get_search_results(search.query, search_id=search.id)
        }

    # TODO: comment
    else:
        response = {
            'results': [{
                'id': search.id,
                'query': search.query,
                'categories': search.context[CATEGORIES],
                'finished_categories': search.context[FINISHED_CATEGORIES],
                'finished': search.finished,
                'finished_at': search.categories.order_by('-modified').first().modified, # TODO: improve hack
            } for search in Search.objects.filter(finished=True, deleted=False).order_by('query', '-created')]
        }

    return JsonResponse(response, status=200)


@require_GET
def search_result_entries(request, search_id):
    """Get entries

    Arguments:
    request -- an HttpRequest object
    """
    print(f"search_result_entries(): request.GET = {request.GET}")
    # Unpack query params
    code = request.GET.get('classification')
    limit = int(request.GET.get('limit', MAX_LIMIT))
    offset = int(request.GET.get('offset', 0))
    assert limit <= MAX_LIMIT # TODO: be more graceful

    # Validate request
    search = _get_search(search_id)
    print(f"search_result_entries(): search = {search}")
    classification = _get_classification(code)
    print(f"search_result_entries(): classification = {classification}")

    # TODO: comment
    entries = SearchResult_Entry.objects.filter(
        search=search,
        category_abbr=classification.category_abbr,
        scopus_source__classifications=classification,
    )
    print(f"search_result_entries(): entries.query = {entries.query}")

    # TODO: comment
    entries_page = entries.order_by('title')[offset:offset+limit]

    # TODO: comment
    response = {
        'count': entries.count(),
        # 'next': ,
        # 'previous': ,
        'results': [{
            'category_abbr': entry.category_abbr,
            'scopus_id': entry.scopus_id,
            'doi': entry.doi,
            'title': entry.title,
            'first_author': entry.first_author,
            'document_type': entry.document_type,
            'publication_name': entry.publication_name,
            'scopus_source_id': entry.scopus_source.id,
        } for entry in entries_page]
    }

    return JsonResponse(response, status=200)


@require_GET
def subject_area_classifications(request):
    """Get Scopus subject area classifications (and parent categories)."""
    categories, classifications = get_subject_area_classifications()
    return JsonResponse({'categories': categories, 'classifications': classifications}, status=200)


def visualizer(request):
    """Returned rendered visualizer template."""
    return render(request, "visualizer.html", context={})


#
# -- Private functions
#


def _search(query, categories=None):
    """Private handler for public `search()` view. See that function for more details. This is for
    testing convenice, so that async jobs can be queued without an HTTP request being involved.
    """
    search_obj = Search.init_search(query, categories)
    job = queue_job(get_search_results, args=(query, categories, search_obj.id), job_timeout=12*60*60)
    return (job.id, search_obj.id)

def _get_search(search_id):
    """TODO: comment"""
    try:
        return Search.objects.filter(finished=True, deleted=False).get(id=search_id)
    except:
        raise Http404(f"Search not found, {search_id}")

def _get_classification(code):
    """TODO: comment"""
    try:
        return ScopusClassification.objects.get(code=code)
    except:
        raise Http404(f"Classification not found, {code}")
