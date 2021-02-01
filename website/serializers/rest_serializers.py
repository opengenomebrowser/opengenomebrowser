import os
import shutil
import json
from website.models import Organism, Genome, Tag, TaxID
from rest_framework import serializers
from datetime import datetime, date


class TaxIDRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxID
        fields = '__all__'


class OrganismRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism
        fields = '__all__'


class GenomesRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genome
        fields = '__all__'


class TagRestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
