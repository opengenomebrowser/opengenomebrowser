import os
import json
from django.core import serializers
from website.models import Strain, Member, Tag, TaxID, Genome


class MemberSerializer():
    @staticmethod
    def export_member(identifier: str) -> dict:
        m = Member.objects.filter(identifier=identifier)
        member_dict = serializers.serialize("json", m, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        member_dict = json.loads(member_dict)[0]['fields']
        member_dict.pop('strain')
        member_dict.pop('representative')
        member_dict.pop('genome')
        member_dict.pop('assembly_longest_scf')
        member_dict.pop('assembly_size')
        member_dict.pop('assembly_nr_scaffolds')
        member_dict.pop('assembly_n50')
        return member_dict

    def import_member(self, raw_member_dict: dict, parent_strain: Strain, is_representative: bool,
                      update_css=True) -> Member:

        member_dict = self.__convert_natural_keys_to_pks(raw_member_dict, parent_strain)

        if Member.objects.filter(identifier=member_dict['identifier']).exists():
            m = Member.objects.get(identifier=member_dict['identifier'])
            current_member_state = self.export_member(member_dict['identifier'])

            if current_member_state == raw_member_dict:
                print(": unchanged")
                m.genome.update()
                if is_representative:
                    parent_strain.set_representative(m)

                m.invariant()
                return m

            print(": update existing")

            genome = m.genome
            member_dict['genome'] = genome.pk

            new_data = '[{"model": "' + Member._meta.label_lower + '", "pk": ' + str(
                m.pk) + ', "fields": ' + json.dumps(member_dict) + '}]'
        else:
            print(": create new")

            genome, created = Genome.objects.get_or_create(identifier=member_dict['identifier'], gbk_file_size=0)
            member_dict['genome'] = genome.pk

            new_data = '[{"model": "' + Member._meta.label_lower + '", "fields": ' + json.dumps(member_dict) + '}]'

        c = 0
        for member in serializers.deserialize("json", new_data):
            assert c == 0, "there can only be one object"
            c += 1

        member.save()
        member = Member.objects.get(identifier=member_dict['identifier'])
        member.update_assembly_info()

        # update genome
        genome.update()

        # Set representative
        if is_representative:
            parent_strain.set_representative(member)

        if update_css:
            Tag.create_tag_color_css()
            TaxID.create_taxid_color_css()

        assert member.invariant()

        return member

    @classmethod
    def __convert_natural_keys_to_pks(self, d: dict, parent_strain: Strain):
        return_d = {}  # create deep copy
        return_d.update(d)

        return_d['strain'] = parent_strain.pk

        return_d['representative'] = None  # assign representative after first save

        return_d['tags'] = [Tag.get_or_create_tag(tag=tag_string).pk for tag_string in return_d['tags']]

        return return_d
