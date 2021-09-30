from django.contrib.admin import ModelAdmin
from django.db.models import JSONField
from prettyjson import PrettyJSONWidget
from django.contrib import messages
import json
from dictdiffer import diff
from datetime import date

from website.models import Genome
from website.serializers import GenomeSerializer


class GenomeAdmin(ModelAdmin):
    change_form_template = 'admin/change_form_genome.html'

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
                       'COG'
                       ]

    exclude = [
        'genomecontent', 'organism',  # primary key, foreign keys
        'assembly_gc', 'assembly_longest_scf', 'assembly_size', 'assembly_nr_scaffolds',  # calculated automatically
        'assembly_n50', 'assembly_gaps', 'assembly_ncount', 'BUSCO_percent_single'  # calculated automatically
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
        for field, data in json_data.items():
            if type(data) is date:
                # convert dates in to strings
                json_data[field] = str(data)

        from db_setup.check_metadata import genome_metadata_is_valid
        try:
            assert genome_metadata_is_valid(data=json_data, path_to_genome=obj.base_path(relative=False),
                                            raise_exception=True), 'check_metadata raised an error'
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Something is wrong with your data: {str(e)}')
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
            messages.add_message(request, messages.INFO, f'Saving the following change: {difference}')
            super().save_model(request, obj, form, change)

            try:
                GenomeSerializer.update_metadata_json(genome=obj, new_data=json_data, who_did_it=request.user.username)
            except Exception as e:
                messages.add_message(request, messages.ERROR, f'Failed to edit the json file! {str(e)}')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
