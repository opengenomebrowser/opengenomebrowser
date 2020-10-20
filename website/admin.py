from django.contrib import admin
from .models import Organism, Genome, Tag, TagDescriptions
from website.models.OrganismSerializer import OrganismSerializer
from website.models.GenomeSerializer import GenomeSerializer
from django.db.models import JSONField
from django.contrib import messages
from prettyjson import PrettyJSONWidget
import json
from dictdiffer import diff


class TagAdmin(admin.ModelAdmin):
    search_fields = ('tag',)

    exclude = (
        'color',
        'text_color_white'
    )

    def save_model(self, request, obj: Tag, form, change):
        try:
            tag_obj = Tag.objects.get(pk=obj.pk)
            # object exists: save and write key to dictionary
            super().save_model(request, obj, form, change)
            TagDescriptions().set_key(key=obj.tag, value=obj.description)
            messages.add_message(request, messages.INFO, 'Changed tag.')
        except Tag.DoesNotExist:
            tag_obj = Tag.objects.create(tag=obj.tag, description=obj.description)
            messages.add_message(request, messages.INFO, 'Created new tag.')

        Tag.create_tag_color_css()


admin.site.register(Tag, TagAdmin)


class OrganismAdmin(admin.ModelAdmin):
    search_fields = ('name',)

    exclude = ('representative',)

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    def save_model(self, request, obj: Organism, form, change):
        os = OrganismSerializer()
        new_dict = form.cleaned_data.copy()
        for i in self.exclude:
            if i in new_dict:
                new_dict.pop(i)

        old_dict = json.load(open(obj.metadata_json))
        for i in self.exclude:
            if i in old_dict:
                old_dict.pop(i)

        new_dict['taxid'] = new_dict['taxid'].id

        # turn tags into set for comparison
        new_dict['tags'] = set(t.tag for t in form.cleaned_data['tags'])
        old_dict['tags'] = set(old_dict['tags'])

        difference = list(diff(old_dict, new_dict))

        if len(difference) == 0:
            messages.add_message(request, messages.INFO, 'No difference!')
        else:
            messages.add_message(request, messages.INFO, F'saving the following change: {difference}')
            super().save_model(request, obj, form, change)

            os.update_metadata_json(organism=obj, who_did_it=request.user.username)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Organism, OrganismAdmin)


class GenomeAdmin(admin.ModelAdmin):
    search_fields = ('identifier',)

    exclude = (
        'genomecontent',
        'representative',
        'organism',
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
        'BUSCO_percent_single'
    )

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    def save_model(self, request, obj: Genome, form, change):
        gs = GenomeSerializer()
        new_dict = form.cleaned_data.copy()
        for i in self.exclude:
            if i in new_dict:
                new_dict.pop(i)

        old_dict = json.load(open(obj.metadata_json))
        for i in self.exclude:
            if i in old_dict:
                old_dict.pop(i)

        # turn tags into set for comparison
        new_dict['tags'] = set(t.tag for t in form.cleaned_data['tags'])
        old_dict['tags'] = set(old_dict['tags'])

        difference = list(diff(old_dict, new_dict))

        if len(difference) == 0:
            messages.add_message(request, messages.INFO, 'No difference!')
        else:
            messages.add_message(request, messages.INFO, F'saving the following change: {difference}')
            super().save_model(request, obj, form, change)

            gs.update_metadata_json(genome=obj, who_did_it=request.user.username)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Genome, GenomeAdmin)
