from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    # TODO:
    return render(request, "index.html")
