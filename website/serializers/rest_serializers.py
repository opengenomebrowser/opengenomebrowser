from website.models import Organism, Genome, Tag, TaxID
from rest_framework import serializers


class TaxIDRestSerializer(serializers.ModelSerializer):
    child_taxids = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        source='get_child_taxids',
        slug_field='id'
    )
    child_organisms = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        source='get_child_organisms',
        slug_field='id'
    )
    child_genomes = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        source='get_child_genomes',
        slug_field='id'
    )

    class Meta:
        model = TaxID
        fields = '__all__'
        lookup_field = 'id'


class OrganismRestSerializer(serializers.ModelSerializer):
    class CustomTaxidSerializer(serializers.ModelSerializer):
        class Meta:
            model = TaxID
            fields = '__all__'

    taxid = CustomTaxidSerializer(
        many=False,
        read_only=True
    )

    class Meta:
        model = Organism
        fields = '__all__'
        lookup_field = 'name'


class GenomesRestSerializer(serializers.ModelSerializer):
    organism = OrganismRestSerializer(
        many=False,
        read_only=True
    )

    class Meta:
        model = Genome
        fields = '__all__'
        lookup_field = 'identifier'


class TagRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        lookup_field = 'tag'
