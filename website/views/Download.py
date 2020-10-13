from django.shortcuts import HttpResponse
from django.http import HttpResponseNotFound
import os
from OpenGenomeBrowser import settings

def download_view(request):
    assert '/../' not in request.path
    assert request.path.startswith('/download/')

    abs_path = os.path.join(settings.GENOMIC_DATABASE, request.path[10:])
    filename = os.path.basename(request.path)

    if settings.DEBUG:
        # in debug mode, simply return the folder/file
        if os.path.isdir(abs_path):
            return HttpResponse('\n'.join(os.listdir(abs_path)))

        elif os.path.isfile(abs_path):
            response = HttpResponse(content_type='text/plain')
            response.content = open(abs_path).read()
            response["Content-Disposition"] = F"attachment; filename={filename}"
            response['Content-Type'] = 'text/plain; charset=utf-8'
            return response

        else:
            return HttpResponseNotFound('<h1>Page not found</h1>')
    else:
        # in production mode, expect nginx redirect setup: https://wellfire.co/learn/nginx-django-x-accel-redirects/
        ##############################################
	    # location ^~ /protected {
	    #     internal;
	    #     autoindex on;
	    #     alias /home/troder/database;
	    # }
        ##############################################$
        redirect_path = request.path.replace('/download/', '/protected/', 1)
        
        response = HttpResponse(200)
        response['X-Accel-Redirect'] = redirect_path

        if os.path.isfile(abs_path):
            response['Content-Disposition'] = F'attachment; filename="{filename}"'
            response['Content-Type'] = 'text/plain; charset=utf-8'
        else:
            response['Content-Type'] = 'text/html; charset=utf-8'

        return response