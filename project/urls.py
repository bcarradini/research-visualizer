from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import visualizer.views


# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/
urlpatterns = [
    path('', visualizer.views.index, name='index'),
    # TODO:
    # path('db/', visualizer.views.db, name='db'),
    # path('admin/', admin.site.urls),
]
