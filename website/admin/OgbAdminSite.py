from django.contrib import admin
from django.urls import path
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import permission_required

from website.admin.MarkdownEditor import markdown_editor_view, markdown_editor_submit
from website.admin.GenomeUpload import GenomeUploadView
from website.admin.AdminActions import download_taxdump, reload_taxids, reload_css, delete_sunburst_cache


class OgbAdminSite(admin.AdminSite):
    site_title = _('OpenGenomeBrowser Admin')
    index_template = 'admin/index.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(route=r'download-taxdump/',
                 view=permission_required('website.add_taxid')(self.admin_view(download_taxdump)),
                 name='download-taxdump'),
            path(route=r'reload-taxids/',
                 view=permission_required('website.add_taxid')(self.admin_view(reload_taxids)),
                 name='reload-taxids'),
            path(route=r'reload-css/',
                 view=self.admin_view(reload_css), name='reload-css'),
            path(route=r'delete-sunburst-cache/',
                 view=permission_required('website.add_genome')(self.admin_view(delete_sunburst_cache)),
                 name='delete-sunburst-cache'),
            path(route=r'markdown-editor/',
                 view=permission_required(['website.change_genome', 'website.change_organism'])(self.admin_view(markdown_editor_view)),
                 name='markdown-editor'),
            path(route=r'markdown-editor/submit/',
                 view=permission_required(['website.change_genome', 'website.change_organism'])(self.admin_view(markdown_editor_submit)),
                 name='markdown-editor-submit'),
            # path(route=r'add-genome/',
            #      view=permission_required(['website.add_genome', 'website.add_organism'])(self.admin_view(GenomeUploadView.as_view())),
            #      name='add-genome'),
        ]
        urls = custom_urls + urls
        return urls
