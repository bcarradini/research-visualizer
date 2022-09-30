"""
Views to support Visualizer URLs
"""
# Standard
import json

# 3rd party
from django.db.models import Count, F
from django.http import JsonResponse, Http404, HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_GET, require_POST

# Internal
from project.worker import queue_job, get_pending_jobs
from visualizer.models import (
    ScopusClassification,
    ScopusSource,
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
    abstract = get_abstract(scopus_id)
    return JsonResponse({'abstract': abstract}, status=200)


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
    job, search = _search(body['query'], body.get('categories'))

    # Respond with job ID and search ID
    return JsonResponse({'search': _serialize_search_job(job, search)}, status=200)


@require_POST
def search_restart(request, search_id):
    """TODO: comment"""
    # Launch asynchronous search
    job, search = _search_restart(search_id)

    # Respond with job ID and search ID
    return JsonResponse({'search': _serialize_search_job(job, search)}, status=200)


@require_http_methods(['GET', 'DELETE'])
def search_results(request, search_id=None):
    """TODO: comments"""
    response = {}

    # If request is for a specific set of search results:
    if search_id:
        # Handle DELETE request
        if request.method == 'DELETE':
            Search.delete_search(search_id)
            response = {
                'deleted': True,
            }
        # Handle GET request
        else:
            search = _get_search(search_id)
            response = {
                'results': get_search_results(search.query, search_id=search.id)
            }

    # If request is for all search results:
    elif request.method == 'GET':
        # Unpack query params
        pending = request.GET.get('pending') in ['true', 'True', True]

        # If pending results have been requested, return a list of search results that are pending
        if pending:
            # Get pending jobs and serialize those pending searches
            pending_jobs = get_pending_jobs()
            pending_searches = _serialize_search_jobs(pending_jobs)
            pending_search_ids = [s['id'] for s in pending_searches]

            # In case of a worker malfunction, get unfinished searches that aren't associated with pending jobs
            stalled_searches = Search.objects.filter(finished=False, deleted=False).exclude(id__in=pending_search_ids)
            stalled_searches = [_serialize_search(search) for search in stalled_searches]

            response = {
                'results': sorted(pending_searches + stalled_searches, key=lambda s: s['created_at'], reverse=True)
            }

        # Otherwise, return a list of search results that are ready (search is finished)
        else:
            searches = Search.objects.filter(finished=True, deleted=False).order_by('query', '-created')
            response = {
                'results': [_serialize_search(search) for search in searches]
            }
    else:
        raise HttpResponseNotAllowed(f"Method not allowed for listing endpoint")

    return JsonResponse(response, status=200)


@require_GET
def search_result_sources(request, search_id):
    """TODO: comments"""
    # Unpack query params
    category_abbr = request.GET.get('category')
    classification_code = request.GET.get('classification')

    # Validate request
    search = _get_search(search_id)
    classification = _get_classification(category_abbr, classification_code)

    # TODO: comment
    if classification:
        sources = ScopusSource.objects.filter(
            classifications=classification,
            entries__search=search,
            entries__category_abbr=classification.category_abbr,
        ).distinct().annotate(count=Count('entries')).values('source_id','source_name','count')
    else:
        sources = SearchResult_Entry.objects.filter(
            search_id=search, category_abbr=category_abbr, scopus_source__isnull=True
        ).values('publication_name').annotate(count=Count('id'),source_name=F('publication_name')).values('source_name','count')

    # TODO: comment
    response = {
        'results': [{
            'id': source.get('source_id'), # TODO: This is confusing; source_id comes from Scopus; it's not our primary key
            'name': source['source_name'],
            'count': source['count'],
        } for source in sources]
    }

    return JsonResponse(response, status=200)


@require_GET
def search_result_entries(request, search_id):
    """TODO: comments"""
    # Unpack query params
    category_abbr = request.GET.get('category')
    classification_code = request.GET.get('classification')
    source_id = request.GET.get('source')
    limit = int(request.GET.get('limit', MAX_LIMIT))
    offset = int(request.GET.get('offset', 0))
    assert limit <= MAX_LIMIT # TODO: be more graceful

    # Validate request
    search = _get_search(search_id)
    classification = _get_classification(category_abbr, classification_code)

    # TODO: comment
    if classification:
        source = _get_source(source_id)
        entries = SearchResult_Entry.objects.filter(
            search=search,
            category_abbr=classification.category_abbr,
            scopus_source=source,
        )
    else:
        entries = SearchResult_Entry.objects.filter(
            search=search,
            category_abbr=category_abbr,
            publication_name=source_id,
        )

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
            'scopus_source_id': entry.scopus_source and entry.scopus_source.id,
        } for entry in entries_page]
    }

    return JsonResponse(response, status=200)


@require_GET
def subject_area_classifications(request):
    """Get Scopus subject area classifications (and parent categories)."""
    # Unpack query params
    cached = request.GET.get('cached') in ['true', 'True', True]

    if cached:
        # Get categories and classifications stores in local database
        categories = {
            c.category_abbr: {'abbr': c.category_abbr, 'name': c.category_name}
            for c in ScopusClassification.objects.distinct('category_abbr').order_by('category_abbr')
        }
        classifications = {
            c.code: {'code': c.code, 'name': c.name, 'category_abbr': c.category_abbr, 'category_name': c.category_name}
            for c in ScopusClassification.objects.distinct('code').order_by('code')
        }
    else:
        # Get categories and classifications straight from Scopus in realtime
        categories, classifications = get_subject_area_classifications()

    return JsonResponse({'categories': categories, 'classifications': classifications}, status=200)


@ensure_csrf_cookie
def visualizer(request):
    """Returned rendered visualizer template."""
    return render(request, "visualizer.html", context={})


#
# -- Private functions
#


def _search(query, categories=None):
    """Private handler for public `search()` view. See that function for more details. This is for
    testing convenience, so that async jobs can be queued without an HTTP request being involved.
    """
    # Initialize search object and queue job for async worker
    search = Search.init_search(query, categories)
    job = queue_job(get_search_results, args=(query, categories, search.id), job_timeout=12*60*60)

    # Record job ID on search object
    search.job_id = job.id
    search.save()

    # Return job and search objects
    return (job, search)

def _search_restart(search_id):
    """Private handler for public `search_restart()` view. See that function for more details. This is for
    testing convenience, so that async jobs can be queued without an HTTP request being involved.
    """
    # Get existing search object and queue job for async worker
    search = _get_search(search_id, finished=False)
    job = queue_job(get_search_results, args=(search.query, None, search.id), job_timeout=12*60*60)

    # Record job ID on search object
    search.job_id = job.id
    search.save()

    return (job, search)

def _get_search(search_id, finished=True):
    """TODO: comment"""
    try:
        return Search.objects.filter(finished=finished, deleted=False).get(id=search_id)
    except:
        raise Http404(f"Search not found, {search_id}")

def _get_classification(category_abbr, classification_code):
    """TODO: comment"""
    try:
        if classification_code == ScopusClassification.UNKNOWN:
            assert category_abbr, f"Category must be specified when classification is {ScopusClassification.UNKNOWN}"
            return None
        return ScopusClassification.objects.get(code=classification_code)
    except:
        raise Http404(f"Classification not found, {classification_code}")

def _get_source(source_id):
    """TODO: comment"""
    try:
        return ScopusSource.objects.get(source_id=source_id)
    except:
        raise Http404(f"Classification not found, {code}")

def _serialize_search(search):
    last_finished_category = search.categories.order_by('-modified').first()
    return {
        'id': search.id,
        'query': search.query,
        'categories': search.context[CATEGORIES],
        'all_categories': set(search.context[CATEGORIES]) == set(ScopusClassification.all_categories()),
        'finished_categories': search.context[FINISHED_CATEGORIES],
        'finished': search.finished,
        'finished_at': last_finished_category and last_finished_category.modified, # TODO: improve hack
        'created_at': search.created,
    }

def _serialize_job(job):
    return {
        'id': job.id,
        'status': job.get_status(),
        'enqueued_at': job.enqueued_at,
        'started_at': job.started_at,
    }

def _serialize_search_job(job, search=None):
    # If search object was not provided, try to locate unfinished search by job ID
    search = search or Search.objects.filter(finished=False, deleted=False).filter(job_id=job.id).first()

    # If search object is available, return serialization
    if search:
        search = _serialize_search(search)
        search['job'] = _serialize_job(job)
        return search

    return None

def _serialize_search_jobs(jobs):
    return list(
        filter(lambda j: j, [_serialize_search_job(job) for job in jobs if job.func == get_search_results])
    )
