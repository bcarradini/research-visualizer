from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

from visualizer.views import index, subject_area_classifications


# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/
urlpatterns = [
    path('', index, name='index'),
    path('subject-area-classifications', subject_area_classifications, name='subject-area-classifications'),
    # TODO:
    # path('db/', visualizer.views.db, name='db'),
    # path('admin/', admin.site.urls),
]
