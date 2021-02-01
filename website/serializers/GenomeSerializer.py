import os
import shutil
import json
from website.models import Organism, Genome, Tag, TaxID, GenomeContent
from rest_framework import serializers
from datetime import datetime, date


class TagField(serializers.StringRelatedField):
    def to_internal_value(self, value):
        return Tag.objects.get_or_create(tag=value).tag


class GenomeSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(validators=[])

    tags = TagField(many=True)

    class Meta:
        model = Genome
        # do not check unique constraints
        extra_kwargs = {
            'name': {'validators': []},
        }

        exclude = [
            # primary key, foreign keys
            'id', 'genomecontent', 'organism',
            # calculated automatically
            'assembly_gc', 'assembly_longest_scf', 'assembly_size', 'assembly_nr_scaffolds', 'assembly_n50',
            'BUSCO_percent_single'
        ]

        set_fields = ['tags']

    def create(self, validated_data, organism: Organism) -> Genome:
        genomecontent, created = GenomeContent.objects.get_or_create(identifier=validated_data['identifier'])
        validated_data['BUSCO_percent_single'] = calculate_busco_single(validated_data)
        validated_data['genomecontent'] = genomecontent
        genome = super().create(validated_data)
        genome.organism = organism
        return genome

    def update(self, instance, validated_data, organism: Organism) -> Genome:
        validated_data['BUSCO_percent_single'] = calculate_busco_single(validated_data)
        genome = super().update(instance, validated_data)
        genome.organism = organism
        return genome

    def is_valid(self, raise_exception=False):
        return super().is_valid(raise_exception)

    @staticmethod
    def update_genomecontent(genome: Genome):
        # update genomecontent
        genome.genomecontent.update()

        # update assembly stats
        genome.update_assembly_info()

    @staticmethod
    def json_matches_genome(genome, json_dict: dict, organism_name: str) -> (bool, dict):
        """
        Test whether Genome object and Organism json-metadata match.

        :returns: True, difference if they match, False, difference if they do not
        :raises: ValidationError if the json-metadata is not valid.
        """
        if type(genome) is str:
            genome = Genome.objects.get(identifier=genome)

        from dictdiffer import diff

        g_s_g = GenomeSerializer(genome)
        genome_state = g_s_g.data
        if 'organism' not in genome_state:
            genome_state['organism'] = genome.organism.name

        g_s_j = GenomeSerializer(data=json_dict)
        g_s_j.is_valid(raise_exception=True)
        json_state = g_s_j.data
        if 'organism' not in json_state:
            json_state['organism'] = organism_name

        for set_field in GenomeSerializer.Meta.set_fields:
            genome_state[set_field] = set(genome_state[set_field])
            json_state[set_field] = set(json_state[set_field])

        difference = list(diff(genome_state, json_state))

        return len(difference) == 0, difference

    @staticmethod
    def export_genome(identifier: str) -> dict:
        o = Genome.objects.get(identifier=identifier)
        genome_dict = GenomeSerializer(o).data
        genome_dict['tags'] = set(genome_dict['tags'])
        return genome_dict

    @classmethod
    def update_metadata_json(cls, genome: Genome, new_data=None, who_did_it='anonymous'):
        date = datetime.now().strftime("%Y_%b_%d_%H_%M_%S")

        if not new_data:
            new_data = cls.export_genome(genome.identifier)

        # ensure data is serializable
        try:
            json.dumps(new_data, default=serialize_fields)
        except json.JSONDecodeError as e:
            raise AssertionError(f'Could not save dictionary as json: {e}')

        # create backup
        bkp_dir = F'{os.path.dirname(genome.metadata_json)}/.bkp'
        os.makedirs(bkp_dir, exist_ok=True)
        bkp_file = F'{bkp_dir}/{date}_{who_did_it}_organism.json'
        shutil.move(src=genome.metadata_json, dst=bkp_file)

        # write new file
        assert not os.path.isfile(genome.metadata_json)

        with open(genome.metadata_json, 'w') as f:
            json.dump(new_data, f, sort_keys=True, indent=4, default=serialize_fields)


def serialize_fields(obj):
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, date):
        return str(obj)
    else:
        raise TypeError(f'Could not serialize {obj}')


def calculate_busco_single(data):
    if 'BUSCO' in data and 'S' in data['BUSCO'] and 'T' in data['BUSCO']:
        busco = data['BUSCO']
        return round(busco['S'] / busco['T'] * 100, 1)
    else:
        return None
