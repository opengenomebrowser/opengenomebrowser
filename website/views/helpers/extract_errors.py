from django.core.handlers.wsgi import WSGIRequest


def extract_errors(request: WSGIRequest, context: dict = None) -> dict:
    if context is None:
        context = {}

    for error in ['error_danger', 'error_warning', 'error_info', 'error_info_bottom']:
        error_messages = request.GET.getlist(error.removeprefix('error_'))
        if error not in context:
            context[error] = error_messages
        else:
            context[error].extend(error_messages)

    return context
