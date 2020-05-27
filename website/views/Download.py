from django.shortcuts import HttpResponse
from django.http import HttpResponseNotFound
import os
from OpenGenomeBrowser import settings


# todo: make faster using nginx https://wellfire.co/learn/nginx-django-x-accel-redirects/
def download_view(request):
    assert '/../' not in request.path
    assert request.path.startswith('/download/')
    path = os.path.join(settings.GENOMIC_DATABASE, request.path[10:])
    if os.path.isdir(path):
        return HttpResponse('\n'.join(os.listdir(path)))

    if os.path.isfile(path):
        response = HttpResponse(content_type='text/plain')
        response.content = open(path).read()
        response["Content-Disposition"] = F"attachment; filename={os.path.basename(path)}"
        return response

    return HttpResponseNotFound('<h1>Page not found</h1>')
