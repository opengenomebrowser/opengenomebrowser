from django.shortcuts import HttpResponse
from django.http import HttpResponseNotFound, JsonResponse
import os
from OpenGenomeBrowser import settings


# in production mode, expect nginx redirect setup: https://wellfire.co/learn/nginx-django-x-accel-redirects/
##############################################
# location ^~ /protected_html {
#     internal;
#     autoindex on;
#     autoindex_format html;
#     alias /path/to/database;
# }
#
# location ^~ /protected_json {
#     internal;
#     autoindex on;
#     autoindex_format json;
#     alias /path/to/database;
# }
##############################################


def files_html(request):
    assert '/../' not in request.path
    url_prefix = '/files_html/'
    protected_prefix = '/protected_html/'
    assert request.path.startswith(url_prefix)

    if settings.DEBUG:
        return return_content_debug(request, url_prefix)
    else:
        return x_accel_redirect(request, url_prefix, protected_prefix)


def files_json(request):
    assert '/../' not in request.path
    url_prefix = '/files_json/'
    protected_prefix = '/protected_json/'
    assert request.path.startswith(url_prefix)

    if settings.DEBUG:
        return return_content_debug(request, url_prefix)
    else:
        return x_accel_redirect(request, url_prefix, protected_prefix)


def return_content_debug(request, url_prefix: str):
    from datetime import datetime

    rel_path = request.path.replace(url_prefix, '', 1)
    abs_path = os.path.join(settings.GENOMIC_DATABASE, rel_path)
    filename = os.path.basename(request.path)

    # in debug mode, simply return the folder/file
    if os.path.isdir(abs_path):
        def jsonify_files(bn):
            path = F'{abs_path}/{bn}'
            stat = os.stat(path)
            if os.path.isfile(path):
                return dict(name=bn, type='file', mtime=datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d-%H:%M'), size=stat.st_size)
            else:
                return dict(name=bn, type='directory', mtime=datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d-%H:%M'))

        files = [jsonify_files(f) for f in os.listdir(abs_path) if not f.startswith('.')]
        return JsonResponse(files, safe=False)

    elif os.path.isfile(abs_path):
        response = HttpResponse(content_type='text/plain')
        response.content = open(abs_path).read()
        response['Content-Disposition'] = F'attachment; filename={filename}'
        response['Content-Type'] = 'text/plain; charset=utf-8'
        return response
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')


def x_accel_redirect(request, url_prefix: str, protected_prefix: str):
    rel_path = request.path.replace(url_prefix, '', 1)
    abs_path = os.path.join(settings.GENOMIC_DATABASE, rel_path)
    filename = os.path.basename(request.path)

    redirect_path = request.path.replace(url_prefix, protected_prefix, 1)

    response = HttpResponse(200)
    response['X-Accel-Redirect'] = redirect_path

    if os.path.isfile(abs_path):
        response['Content-Disposition'] = F'attachment; filename="{filename}"'
        response['Content-Type'] = 'text/plain; charset=utf-8'
    else:
        response['Content-Type'] = 'text/html; charset=utf-8'

    return response
