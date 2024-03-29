def contains_data(request, key: str) -> bool:
    return key in request.GET or key in request.POST


def contains_all(request, keys: [str]) -> bool:
    return all(key in request.GET or key in request.POST for key in keys)


def extract_data(request, key: str, list: bool = False, sep: str = ' ', raise_errors: bool = False) -> [str]:
    if key in request.GET:
        data = request.GET[key]
    elif key in request.POST:
        data = request.POST[key]
    else:
        if raise_errors:
            raise KeyError(
                f'Could not extract "{key}" from request. '
                f'Submitted keys: {request.GET.keys()} (GET), '
                f'{request.POST.keys()} (POST)'
            )
        else:
            return None

    if list:
        return [e.replace('!!!', ' ') for e in data.split(sep)]
    else:
        return data.replace('!!!', ' ')


def extract_data_or(request, key: str, list: bool = False, sep: str = ' ', default=None):
    try:
        data = extract_data(request=request, key=key, list=list, sep=sep, raise_errors=True)
        if data is not None and len(data) > 0:  # return only if there is something
            return data
    except:
        pass
    return default
