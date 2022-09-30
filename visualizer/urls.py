"""
Visualizer app URLs
"""
# 3rd party
from django.urls import path, include

# Internal
from visualizer.views import (
    abstract,
    search,
    search_restart,
    search_results,
    search_result_entries,
    search_result_sources,
    subject_area_classifications,
    visualizer,
)


# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/
urlpatterns = [
    path('abstract/<int:scopus_id>', abstract, name='abstract'),
    path('search', search, name='search'),
    path('search/<int:search_id>/restart', search_restart, name='search_restart'),
    path('search-results', search_results, name='search_results'),
    path('search-results/<int:search_id>', search_results, name='search_results'),
    path('search-results/<int:search_id>/sources', search_result_sources, name='search_result_sources'),
    path('search-results/<int:search_id>/entries', search_result_entries, name='search_result_entries'),
    path('subject-area-classifications', subject_area_classifications, name='subject-area-classifications'),
    path('', visualizer, name='visualizer'),
]
