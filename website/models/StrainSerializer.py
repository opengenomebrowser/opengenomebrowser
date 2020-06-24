from website.models import Strain, Tag, TaxID
import json
from django.core import serializers


class StrainSerializer():
    def export_strain(self, name: str) -> dict:
        s_qs = Strain.objects.filter(name=name)
        s = s_qs.first()
        strain_dict = serializers.serialize("json", s_qs, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        strain_dict = json.loads(strain_dict)[0]['fields']

        if hasattr(s, 'representative'):
            representative: str = s.representative.identifier
            strain_dict['representative'] = representative
        else:
            strain_dict['representative'] = "ERROR"

        return strain_dict

    def import_strain(self, raw_strain_dict: dict, update_css=True) -> Strain:
        strain_dict = self.__convert_natural_keys_to_pks(raw_strain_dict)

        strain_dict.pop('representative')

        strain_json = json.dumps(strain_dict)

        if Strain.objects.filter(name=strain_dict['name']).exists():
            s = Strain.objects.get(name=strain_dict['name'])

            current_strain_state = self.export_strain(strain_dict['name'])

            if current_strain_state == raw_strain_dict:
                print(": unchanged")
                return s

            print(": update existing")
            s = Strain.objects.get(name=strain_dict['name'])
            new_data = '[{"model": "' + Strain._meta.label_lower + '", "pk": ' + str(
                s.pk) + ', "fields": ' + strain_json + '}]'
        else:
            print(": create new")
            new_data = '[{"model": "' + Strain._meta.label_lower + '", "fields": ' + strain_json + '}]'

        c = 0
        for strain in serializers.deserialize("json", new_data):
            c += 1
        assert c == 1, "there can only be one object"

        strain.save()

        if update_css:
            Tag.create_tag_color_css()
            TaxID.create_taxid_color_css()

        return Strain.objects.get(name=strain_dict['name'])

    @classmethod
    def __convert_natural_keys_to_pks(self, d: dict):
        return_d = {}  # create deep copy
        return_d.update(d)

        return_d['tags'] = [Tag.objects.get_or_create_tag(tag=tag_string).id for tag_string in return_d['tags']]
        return_d['taxid'] = TaxID.get_or_create(return_d['taxid']).pk
        return return_d
