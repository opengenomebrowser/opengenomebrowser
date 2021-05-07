from django.contrib.admin import ModelAdmin
from django.db.models import JSONField
from prettyjson import PrettyJSONWidget
from django.contrib import messages
import json
from dictdiffer import diff

from website.models import Organism, Genome
from website.serializers import OrganismSerializer


class OrganismAdmin(ModelAdmin):
    change_form_template = 'admin/change_form_organism.html'

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

        # load current json, turn tags into set
        old_dict = json.load(open(obj.metadata_json))
        old_dict['tags'] = set(old_dict['tags'])

        # did something change?
        difference = list(diff(json_data, old_dict))
        match = len(difference) == 0

        if match:
            messages.add_message(request, messages.INFO, 'No difference!')
        else:
            messages.add_message(request, messages.INFO, F'Saving the following change: {difference}')
            super().save_model(request, obj, form, change)

            try:
                OrganismSerializer.update_metadata_json(organism=obj, new_data=json_data, who_did_it=request.user.username)
            except Exception as e:
                messages.add_message(request, messages.ERROR, f'Failed to edit the json file! {str(e)}')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
