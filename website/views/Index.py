from django.shortcuts import render, HttpResponse

from website.models.KeggMap import KeggMap


def index_view(request):
    context = {}

    return render(request, 'website/index.html', context)
