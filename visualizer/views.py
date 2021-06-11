from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting

def index(request):
    # TODO:
    return render(request, "index.html")
