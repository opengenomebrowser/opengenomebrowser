import os
import json
from django.core import serializers
from website.models import Strain, Genome, Tag, TaxID, GenomeContent


class GenomeSerializer():
    @staticmethod
    def export_genome(identifier: str) -> dict:
        g = Genome.objects.filter(identifier=identifier)
        genome_dict = serializers.serialize("json", g, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        genome_dict = json.loads(genome_dict)[0]['fields']
        genome_dict.pop('strain')
        genome_dict.pop('representative')
        genome_dict.pop('genomecontent')
        genome_dict.pop('assembly_longest_scf')
        genome_dict.pop('assembly_size')
        genome_dict.pop('assembly_nr_scaffolds')
        genome_dict.pop('assembly_n50')
        genome_dict.pop('cds_tool_n_genes')
        genome_dict.pop('BUSCO_percent_single')
        return genome_dict

    def import_genome(self, raw_genomes_dict: dict, parent_strain: Strain, is_representative: bool,
                      update_css=True) -> Genome:

        genome_dict = self.__convert_natural_keys_to_pks(raw_genomes_dict, parent_strain)

        if Genome.objects.filter(identifier=genome_dict['identifier']).exists():
            g = Genome.objects.get(identifier=genome_dict['identifier'])
            current_genome_state = self.export_genome(genome_dict['identifier'])

            if current_genome_state == raw_genomes_dict:
                print(": unchanged")
                g.genomecontent.update()
                if is_representative:
                    parent_strain.set_representative(g)

                g.invariant()
                return g

            print(": update existing")

            genomecontent = g.genomecontent
            genome_dict['genomecontent'] = genomecontent.pk

            new_data = '[{"model": "' + Genome._meta.label_lower + '", "pk": ' + str(
                g.pk) + ', "fields": ' + json.dumps(genome_dict) + '}]'
        else:
            print(": create new")

            genomecontent, created = GenomeContent.objects.get_or_create(identifier=genome_dict['identifier'])
            genome_dict['genomecontent'] = genomecontent.pk

            new_data = '[{"model": "' + Genome._meta.label_lower + '", "fields": ' + json.dumps(genome_dict) + '}]'

        c = 0
        for genome in serializers.deserialize("json", new_data):
            assert c == 0, "there can only be one object"
            c += 1

        genome.save()
        genome = Genome.objects.get(identifier=genome_dict['identifier'])
        genome.update_assembly_info()

        # update genomecontent
        genomecontent.update()

        # Set representative
        if is_representative:
            parent_strain.set_representative(genome)

        if update_css:
            Tag.create_tag_color_css()
            TaxID.create_taxid_color_css()

        assert genome.invariant()

        return genome

    @classmethod
    def __convert_natural_keys_to_pks(self, d: dict, parent_strain: Strain):
        return_d = {}  # create deep copy
        return_d.update(d)

        return_d['strain'] = parent_strain.pk

        return_d['representative'] = None  # assign representative after first save

        return_d['tags'] = [Tag.objects.get_or_create_tag(tag=tag_string).pk for tag_string in return_d['tags']]

        if 'S' in return_d['BUSCO'] and 'T' in return_d['BUSCO']:
            return_d['BUSCO_percent_single'] = round(return_d['BUSCO']['S'] / return_d['BUSCO']['T'], 1)
            print(return_d['BUSCO_percent_single'])
        else:
            return_d['BUSCO_percent_single'] = None

        return return_d
