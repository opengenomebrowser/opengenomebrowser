import os
from django.db.models import Model
from website.models import *

LOGIN_REQUIRED = os.environ.get('LOGIN_REQUIRED', 'true').lower() == 'true'


def get_placeholder(model: Model, alt_message: str = None) -> str:
    if model.objects.exists():
        return f"e.g. {model.objects.order_by('?')[0]}"
    else:
        if alt_message:
            return alt_message
        return f'no {model.__name__} found in the database'


def add_placeholders(request):
    if LOGIN_REQUIRED and not request.user.is_authenticated:
        placeholder_fn = lambda m: 'NOT AUTHENTICATED'
    else:
        placeholder_fn = get_placeholder

    return {
        'placeholders': {
            'genome': placeholder_fn(Genome),
            'gene': placeholder_fn(Gene),
            'annotation': placeholder_fn(Annotation),
            'tag': placeholder_fn(Tag),
            'pathway': placeholder_fn(PathwayMap)
        }
    }
