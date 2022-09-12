"""
Views to support Visualizer URLs
"""
# Standard
import json

# 3rd party
from django.db.models import Count, F
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

# Internal
from project.worker import queue_job
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
    print(f"TEMP: abstract(): abstract = {abstract}")
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
    return JsonResponse({'job': {'id': job.id}, 'search': _serialize_search(search)}, status=200)


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
        searches = Search.objects.filter(finished=True, deleted=False).order_by('query', '-created')
        response = {
            'results': [_serialize_search(search) for search in searches]
        }

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
    return (job, search_obj)

def _get_search(search_id):
    """TODO: comment"""
    try:
        return Search.objects.filter(finished=True, deleted=False).get(id=search_id)
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
        'started_at': search.created,
    }
