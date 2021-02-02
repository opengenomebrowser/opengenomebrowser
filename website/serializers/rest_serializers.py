from website.models import Organism, Genome, Tag, TaxID
from rest_framework import serializers


class TaxIDRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxID
        fields = '__all__'
        lookup_field = 'id'

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
        slug_field='name'
    )
    child_genomes = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        source='get_child_genomes',
        slug_field='identifier'
    )


class OrganismRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism
        fields = '__all__'
        lookup_field = 'name'

    class CustomTaxidSerializer(serializers.ModelSerializer):
        class Meta:
            model = TaxID
            fields = '__all__'

    taxid = CustomTaxidSerializer(
        many=False,
        read_only=True
    )

    class CustomGenomeSerializer(serializers.ModelSerializer):
        class Meta:
            model = Genome
            fields = '__all__'

    child_genomes = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        source='genome_set.all',
        slug_field='identifier'
    )


class GenomesRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genome
        fields = '__all__'
        lookup_field = 'identifier'

    organism = OrganismRestSerializer(
        many=False,
        read_only=True
    )


class TagRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        lookup_field = 'tag'
