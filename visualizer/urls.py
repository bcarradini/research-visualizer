"""
Visualizer app URLs
"""
# 3rd party
from django.urls import path, include

# Internal
from visualizer.views import (
    abstract,
    search,
    search_results,
    subject_area_classifications,
    visualizer,
)


# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/
urlpatterns = [
    path('abstract/<int:scopus_id>', abstract, name='abstract'),
    path('search', search, name='search'),
    path('search-results', search_results, name='search_results'),
    path('search-results/<int:search_id>', search_results, name='search_results'),
    path('subject-area-classifications', subject_area_classifications, name='subject-area-classifications'),
    path('', visualizer, name='visualizer'),
]
