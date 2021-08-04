from django.contrib.admin import ModelAdmin
from django.contrib import messages
from django.http import HttpResponseRedirect

from website.models import TaxID
from lib.get_tax_info.get_tax_info import TaxIdNnotFoundError


class TaxIdAdmin(ModelAdmin):
    change_list_template = 'admin/change_list_taxid.html'

    search_fields = ['taxscientificname', 'id']
    fields = ['id', 'taxscientificname', 'rank', 'parent']
    readonly_fields = ['taxscientificname', 'rank', 'parent']

    def save_model(self, request, obj: TaxID, form, change):
        TaxID.get_or_create(taxid=obj.id)
        TaxID.create_taxid_color_css()

    def changeform_view(self, request, *args, **kwargs):
        try:
            return super().changeform_view(request, *args, **kwargs)
        except TaxIdNnotFoundError as e:
            messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')
            return HttpResponseRedirect(request.path)
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')
            return HttpResponseRedirect(request.path)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
