from django.shortcuts import HttpResponse
from django.http import HttpResponseNotFound, JsonResponse, StreamingHttpResponse
from wsgiref.util import FileWrapper

import os
from OpenGenomeBrowser import settings
from mimetypes import guess_type


# in production mode, expect nginx redirect setup: https://wellfire.co/learn/nginx-django-x-accel-redirects/
##############################################
# location ^~ /protected_html {
#     internal;
#     autoindex on;
#     autoindex_format html;
#     alias /folder_structure;
# }
#
# location ^~ /protected_json {
#     internal;
#     autoindex on;
#     autoindex_format json;
#     alias /folder_structure;
# }
#
# location ^~ /protected_cache {
#     internal;
#     autoindex on;
#     autoindex_format html;
#     alias /tmp/ogb-cache;
# }
##############################################


def files_html(request):
    return _return_files(
        request_path=request.path,
        url_prefix='/files_html/',
        protected_prefix='/protected_html/',
        fs_prefix=settings.FOLDER_STRUCTURE
    )


def files_json(request):
    return _return_files(
        request_path=request.path,
        url_prefix='/files_json/',
        protected_prefix='/protected_json/',
        fs_prefix=settings.FOLDER_STRUCTURE
    )


def files_cache(request):
    return _return_files(
        request_path=request.path,
        url_prefix='/files_cache/',
        protected_prefix='/protected_cache/',
        fs_prefix=settings.CACHE_DIR
    )


def _return_files(request_path: str, url_prefix: str, protected_prefix: str, fs_prefix: str):
    assert '/../' not in request_path
    assert request_path.startswith(url_prefix)
    rel_path = request_path[len(url_prefix):]
    abs_path = os.path.join(fs_prefix, rel_path)
    redirect_path = os.path.join(protected_prefix, rel_path)
    filename = os.path.basename(request_path)

    if settings.DEBUG:
        return _return_content_debug(abs_path=abs_path)
    else:
        return _x_accel_redirect(abs_path=abs_path, redirect_path=redirect_path, filename=filename)


def _return_content_debug(abs_path: str):
    from datetime import datetime

    # in debug mode, simply return the folder/file
    if os.path.isdir(abs_path):
        def jsonify_files(bn):
            """creates a dict of the content of every folder, mimicking nginx json output"""
            path = f'{abs_path}/{bn}'
            stat = os.stat(path)
            if os.path.isfile(path):
                return dict(name=bn, type='file', mtime=datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d-%H:%M'), size=stat.st_size)
            else:
                return dict(name=bn, type='directory', mtime=datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d-%H:%M'),
                            content=os.listdir(path))

        files = [jsonify_files(f) for f in os.listdir(abs_path) if not f.startswith('.')]
        return JsonResponse(files, safe=False)

    elif os.path.isfile(abs_path):
        content_type, content_encoding = guess_type(abs_path)
        response = StreamingHttpResponse(
            FileWrapper(open(abs_path, 'rb'), blksize=8192),
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename={os.path.basename(abs_path)}'
        response['Content-Length'] = os.path.getsize(abs_path)
        return response
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')


def _x_accel_redirect(abs_path: str, redirect_path: str, filename: str):
    response = HttpResponse(200)
    response['X-Accel-Redirect'] = redirect_path

    if os.path.isfile(abs_path):
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        content_type, content_encoding = guess_type(abs_path)
        response['Content-Type'] = f'{content_type}; charset={content_encoding}'
    else:
        response['Content-Type'] = 'text/html; charset=utf-8'

    return response
