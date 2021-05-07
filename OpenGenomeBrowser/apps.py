from django.contrib.admin.apps import AdminConfig


class OgbAdminConfig(AdminConfig):
    default_site = 'website.admin.OgbAdminSite.OgbAdminSite'
