from django.contrib import admin
from .models import Organism, Genome, Tag, TagDescriptions
from website.serializers import OrganismSerializer
from website.serializers import GenomeSerializer
from django.db.models import JSONField
from django.contrib import messages
from django.core.exceptions import ValidationError
from prettyjson import PrettyJSONWidget
import json
from dictdiffer import diff


class TagAdmin(admin.ModelAdmin):
    search_fields = ['tag']

    exclude = ['color', 'text_color_white']

    def save_model(self, request, obj: Tag, form, change):
        # to change the tag name, the change would have to be propagated to all metadata json files!
        if form.initial['tag'] != form.cleaned_data['tag']:
            messages.warning(request, messages.INFO, F'Changing tag names is currently not supported.')
            return

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
    search_fields = ['name']

    readonly_fields = ['name']

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    def render_change_form(self, request, context, *args, **kwargs):
        # ensure only genomes that belong to organism may be chosen.
        organism = kwargs['obj']
        context['adminform'].form.fields['representative'].queryset = Genome.objects.filter(organism=organism)
        return super().render_change_form(request, context, *args, **kwargs)

    def save_model(self, request, obj: Organism, form, change):
        # turn form into organism.json
        json_data = form.cleaned_data.copy()
        json_data['name'] = obj.name
        json_data['tags'] = set(t.tag for t in json_data['tags'])
        json_data['taxid'] = json_data['taxid'].id
        json_data['representative'] = json_data['representative'].identifier

        # ensure that representative genome exists and belongs to organism
        try:
            r = Genome.objects.get(identifier=json_data['representative'])
            assert r.organism.name == obj.name
        except Genome.DoesNotExist:
            messages.add_message(request, messages.INFO, F'Representative ({json_data["representative"]}) does not exist!')
            return
        except AssertionError:
            messages.add_message(request, messages.INFO, F'Representative ({json_data["representative"]}) does not belong to this organism!')
            return

        # did something change?
        match, difference = OrganismSerializer.json_matches_organism(organism=obj.name, json_dict=json_data)

        if match:
            messages.add_message(request, messages.INFO, 'No difference!')
        else:
            messages.add_message(request, messages.INFO, F'Saving the following change: {difference}')
            super().save_model(request, obj, form, change)

            OrganismSerializer.update_metadata_json(organism=obj, new_data=json_data, who_did_it=request.user.username)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Organism, OrganismAdmin)


class GenomeAdmin(admin.ModelAdmin):
    search_fields = ['identifier']

    readonly_fields = ['identifier',
                       'cds_tool_faa_file',
                       'cds_tool_gbk_file',
                       'cds_tool_gff_file',
                       'cds_tool_ffn_file',
                       'cds_tool_sqn_file',
                       'custom_annotations',
                       'assembly_fasta_file',
                       'BUSCO',
                       'BUSCO_percent_single'
                       ]

    exclude = [
        'genomecontent', 'organism',  # primary key, foreign keys
        'assembly_longest_scf', 'assembly_size', 'assembly_nr_scaffolds', 'assembly_n50'  # calculated automatically
    ]

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    def save_model(self, request, obj: Genome, form, change):
        # turn form into organism.json
        json_data = form.cleaned_data.copy()
        json_data['tags'] = set(t.tag for t in json_data['tags'])
        for field in self.readonly_fields:
            assert field not in json_data
            json_data[field] = getattr(obj, field)

        # did something change?
        match, difference = GenomeSerializer.json_matches_genome(genome=obj, json_dict=json_data, organism_name=obj.organism.name)

        if match:
            messages.add_message(request, messages.INFO, 'No difference!')
        else:
            messages.add_message(request, messages.INFO, F'Saving the following change: {difference}')
            super().save_model(request, obj, form, change)

            GenomeSerializer.update_metadata_json(genome=obj, new_data=json_data, who_did_it=request.user.username)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Genome, GenomeAdmin)
