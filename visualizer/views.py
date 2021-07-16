

# Standard

# 3rd party
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
import requests

# Internal

# Constants


#
# -- Public functions
#


def index(request):
    return render(request, "index.html", context={})


def subject_area_classifications(request):
    categories, classifications = _get_subject_area_categories_and_classifications()
    return JsonResponse({'categories': categories, 'classifications': classifications}, status=200)


#
# -- Private functions
#

def _get_subject_area_categories_and_classifications():
    # Request Scopus subject area classifications
    url = f"https://api.elsevier.com/content/subject/scopus?apiKey={settings.SCOPUS_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()

    # Unpack successful response
    classifications = response.json()['subject-classifications']['subject-classification']
    categories = list(set(map(lambda c: c['abbrev'], classifications)))
    print(f"TEMP: subject_area_classifications(): classifications = {classifications}")
    print(f"TEMP: subject_area_classifications(): categories = {categories}")

    return (categories, classifications)
