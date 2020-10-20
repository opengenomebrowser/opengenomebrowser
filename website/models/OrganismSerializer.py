from website.models import Organism, Tag, TaxID
import os
import shutil
import json
from django.core import serializers


class OrganismSerializer():
    @staticmethod
    def export_organism(name: str) -> dict:
        o_qs = Organism.objects.filter(name=name)
        o = o_qs.first()
        organism_dict = serializers.serialize("json", o_qs, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        organism_dict = json.loads(organism_dict)[0]['fields']

        if hasattr(o, 'representative'):
            representative: str = o.representative.identifier
            organism_dict['representative'] = representative
        else:
            organism_dict['representative'] = "ERROR"

        organism_dict['tags'] = set(organism_dict['tags'])

        return organism_dict

    def import_organism(self, raw_organism_dict: dict, update_css=True) -> Organism:
        if 'tags' in raw_organism_dict:
            raw_organism_dict['tags'] = set(raw_organism_dict['tags'])

        organism_dict = self._convert_natural_keys_to_pks(raw_organism_dict)
        organism_dict.pop('representative')

        organism_json = json.dumps(organism_dict, default=set_to_list)

        if Organism.objects.filter(name=organism_dict['name']).exists():
            o = Organism.objects.get(name=organism_dict['name'])

            current_organism_state = self.export_organism(organism_dict['name'])

            if current_organism_state == raw_organism_dict:
                print(" :: unchanged")
                return o

            print(" :: update existing")
            o = Organism.objects.get(name=organism_dict['name'])
            new_data = '[{"model": "' + Organism._meta.label_lower + '", "pk": ' + str(
                o.pk) + ', "fields": ' + organism_json + '}]'
        else:
            print(" :: create new")
            new_data = '[{"model": "' + Organism._meta.label_lower + '", "fields": ' + organism_json + '}]'

        c = 0
        for organism in serializers.deserialize("json", new_data):
            c += 1
        assert c == 1, "there can only be one object"

        organism.save()

        if update_css:
            Tag.create_tag_color_css()
            TaxID.create_taxid_color_css()

        return Organism.objects.get(name=organism_dict['name'])

    @classmethod
    def _convert_natural_keys_to_pks(self, d: dict):
        return_d = {}  # create deep copy
        return_d.update(d)

        return_d['tags'] = set(Tag.objects.get_or_create(tag=tag_string).tag for tag_string in return_d['tags'])
        return_d['taxid'] = TaxID.get_or_create(return_d['taxid']).pk
        return return_d

    @classmethod
    def update_metadata_json(cls, organism: Organism, who_did_it='anonymous'):
        from datetime import datetime
        date = datetime.now().strftime("%Y_%b_%d_%H_%M_%S")

        new_data = cls.export_organism(organism.name)

        # create backup
        bkp_dir = F'{os.path.dirname(organism.metadata_json)}/.bkp'
        os.makedirs(bkp_dir, exist_ok=True)
        bkp_file = F'{bkp_dir}/{date}_{who_did_it}_organism.json'
        shutil.move(src=organism.metadata_json, dst=bkp_file)

        # write new file
        assert not os.path.isfile(organism.metadata_json)
        with open(organism.metadata_json, 'w') as f:
            json.dump(new_data, f, sort_keys=True, indent=4, default=set_to_list)


def set_to_list(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError
