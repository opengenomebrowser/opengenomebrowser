from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve, reverse
from django.http import HttpResponseRedirect
from OpenGenomeBrowser import settings
from urllib.parse import quote


class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings by setting a tuple of routes to ignore

    https://stackoverflow.com/questions/3214589/56579091#56579091
    """

    def process_request(self, request):
        assert hasattr(request, 'user'), """
        The Login Required middleware needs to be after AuthenticationMiddleware.
        Also make sure to include the template context_processor:
        'django.contrib.auth.context_processors.auth'."""

        if not request.user.is_authenticated:
            current_route_name = resolve(request.path_info).url_name

            if not current_route_name in settings.AUTH_EXEMPT_ROUTES:
                login_url = reverse(settings.AUTH_LOGIN_ROUTE)
                next = request.get_full_path()
                next = quote(next)  # replace special characters using %xx escape
                return HttpResponseRedirect(f'{login_url}?next={next}')
