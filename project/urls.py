"""
Project app URLs
"""
# 3rd party
from django.urls import path, include
from django.contrib import admin

# Auto-discover installed apps
admin.autodiscover()

from visualizer import urls as visualizer_urls


# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/
urlpatterns = [
    path(r'', include((visualizer_urls, 'ihs'), namespace='visualizer')),
    # TODO:
    # path('db/', visualizer.views.db, name='db'),
    # path('admin/', admin.site.urls),
]
