from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

from visualizer.views import index, search, subject_area_classifications


# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/
urlpatterns = [
    path('search', search, name='search'),
    path('subject-area-classifications', subject_area_classifications, name='subject-area-classifications'),
    path('', index, name='index'),
    # TODO:
    # path('db/', visualizer.views.db, name='db'),
    # path('admin/', admin.site.urls),
]
