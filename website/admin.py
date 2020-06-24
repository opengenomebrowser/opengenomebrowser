from django.contrib import admin
from .models import Genome, Tag
from django.contrib.postgres.fields import JSONField
from prettyjson import PrettyJSONWidget


class TagAdmin(admin.ModelAdmin):
    exclude = (
        'color',
        'text_color_white'
    )

    def save_model(self, request, obj: Tag, form, change):
        print('xxx')
        obj.color = 'abc'
        obj.text_color_white = True
        super(TagAdmin, self).save_model(request, obj, form, change)


admin.site.register(Tag, TagAdmin)


class GenomeAdmin(admin.ModelAdmin):
    exclude = (
        'genomecontent',
        'representative',
        'strain',
        'cds_tool_faa_file',
        'cds_tool_gbk_file',
        'cds_tool_gff_file',
        'cds_tool_ffn_file',
        'cds_tool_sqn_file',
        'custom_annotations',
        'assembly_fasta_file',
        'assembly_longest_scf',
        'assembly_size',
        'assembly_nr_scaffolds',
        'assembly_n50',
        'nr_replicons'
    )

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Genome, GenomeAdmin)
