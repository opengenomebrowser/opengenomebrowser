"""OpenGenomeBrowser URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth.views import LoginView


class MyLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_context_data(self, **kwargs):
        from OpenGenomeBrowser import settings
        context = super().get_context_data(**kwargs)
        if hasattr(settings, 'LOGIN_MESSAGE'):
            context['login_message'] = settings.LOGIN_MESSAGE
        return context


urlpatterns = [
                  path('accounts/login/', MyLoginView.as_view(), name="login"),
                  path('admin/', admin.site.urls),
                  path('accounts/', include('django.contrib.auth.urls')),
                  path('invitations/', include('invitations.urls', namespace='invitations')),
                  path('', include('website.urls')),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    # Serving files uploaded by a user during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
