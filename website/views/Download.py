from django.shortcuts import HttpResponse
from django.http import HttpResponseNotFound
import os
from OpenGenomeBrowser import settings

def download_view(request):
    assert '/../' not in request.path
    assert request.path.startswith('/download/')

    if settings.DEBUG:
        # in debug mode, simply return the folder/file
        path = os.path.join(settings.GENOMIC_DATABASE, request.path[10:])
        if os.path.isdir(path):
            return HttpResponse('\n'.join(os.listdir(path)))

        if os.path.isfile(path):
            response = HttpResponse(content_type='text/plain')
            response.content = open(path).read()
            response["Content-Disposition"] = F"attachment; filename={os.path.basename(path)}"
            return response

        return HttpResponseNotFound('<h1>Page not found</h1>')
    else:
        # in production mode, expect nginx redirect setup: https://wellfire.co/learn/nginx-django-x-accel-redirects/
        ##############################################
        # location /download/ {
        #   internal;
        #   alias   /path/to/database;
        # }
        ##############################################$
        filename = os.path.basename(request.path)
        new_path = request.path.replace('/download/', '/protected/', 1)
        
        response = HttpResponse()
        del response['Content-Type']
        del response['Accept-Ranges']
        del response['Set-Cookie']
        del response['Cache-Control']
        del response['Expires']
        response['X-Accel-Redirect'] = new_path
        response['Content-Disposition'] = F'attachment; filename="{filename}"'
        return response