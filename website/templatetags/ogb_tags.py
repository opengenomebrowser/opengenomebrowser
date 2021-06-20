from django import template

register = template.Library()


@register.simple_tag
def define(val=None):
    return val


@register.simple_tag(takes_context=False)
def split_date(date: str):
    return date.split(':')


@register.simple_tag(takes_context=False)
def get_item(dictionary: dict, *keys: str):
    res = dictionary
    for key in keys:
        res = res[key]
    return res


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    https://www.caktusgroup.com/blog/2018/10/18/filtering-and-pagination-django/
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()


@register.simple_tag
def cur_plus_n_st_last(n, cur, last, *args, **kwargs):
    return cur + n < last
