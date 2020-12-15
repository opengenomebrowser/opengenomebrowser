from website.models import Organism, Genome, Tag, TaxID
import os
import shutil
import json
from rest_framework import serializers


class TagField(serializers.StringRelatedField):
    def to_internal_value(self, value):
        return Tag.objects.get_or_create(tag=value).tag


class TaxidField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, value):
        return TaxID.get_or_create(taxid=value)

    def queryset(self):
        TaxID.objects.all()


class OrganismSerializer(serializers.ModelSerializer):
    representative = serializers.CharField()

    tags = TagField(many=True)

    taxid = TaxidField(many=False)

    def validate(self, data):
        organism = data['name']
        representative = self.initial_data['representative']
        if not representative.startswith(organism):
            raise serializers.ValidationError(F'Name of representative ({representative}) must start with name of organism ({organism})')
        return data

    class Meta:
        model = Organism
        fields = ['name', 'alternative_name', 'restricted', 'taxid', 'tags', 'representative']

        set_fields = ['tags']

        # do not check unique constraints
        extra_kwargs = {
            'name': {'validators': []},
        }

    def create(self, validated_data) -> Organism:
        validated_data['representative'] = None
        organism = super().create(validated_data)
        return organism

    def update(self, instance, validated_data, representative_isnull=False) -> Organism:
        # ensure the name has not changed
        if instance.name != validated_data['name']:
            raise serializers.ValidationError('"name" of organism may not be changed!')

        if representative_isnull:
            validated_data['representative'] = None
        else:
            validated_data['representative'] = Genome.objects.get(identifier=validated_data['representative'])
        organism = super().update(instance, validated_data)
        return organism

    @staticmethod
    def json_matches_organism(organism, json_dict: dict) -> (bool, dict):
        """
        Test whether Organism object and Organism json-metadata match.

        :returns: True, difference if they match, False, difference if they do not
        :raises: ValidationError if the json-metadata is not valid.
        """
        if type(organism) is str:
            organism = Organism.objects.get(name=organism)

        from dictdiffer import diff

        o_s_o = OrganismSerializer(organism)
        organism_state = o_s_o.data

        o_s_j = OrganismSerializer(data=json_dict)
        o_s_j.is_valid(raise_exception=True)
        json_state = o_s_j.data

        for set_field in OrganismSerializer.Meta.set_fields:
            organism_state[set_field] = set(organism_state[set_field])
            json_state[set_field] = set(json_state[set_field])

        difference = list(diff(organism_state, json_state))

        return len(difference) == 0, difference

    @staticmethod
    def export_organism(name: str) -> dict:
        o = Organism.objects.get(name=name)
        organism_dict = OrganismSerializer(o).data
        organism_dict['tags'] = set(organism_dict['tags'])
        return organism_dict

    @classmethod
    def update_metadata_json(cls, organism: Organism, new_data=None, who_did_it='anonymous'):
        # ensure data is serializable
        try:
            json.dumps(new_data, default=set_to_list)
        except json.JSONDecodeError as e:
            raise AssertionError(f'Could not save dictionary as json: {e}')

        from datetime import datetime
        date = datetime.now().strftime("%Y_%b_%d_%H_%M_%S")

        if not new_data:
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
    raise TypeError(f'Could not serialize {obj}')
