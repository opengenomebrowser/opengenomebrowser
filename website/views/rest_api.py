from website.models import Genome, Organism, TaxID
from rest_framework import viewsets
from rest_framework import permissions
from website.serializers.rest_serializers import *


class TaxIDViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = TaxID.objects.all().order_by('id')
    serializer_class = TaxIDRestSerializer


class GenomeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Genome.objects.all().order_by('identifier')
    serializer_class = GenomesRestSerializer


class OrganismViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Organism.objects.all().order_by('name')
    serializer_class = OrganismRestSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Tag.objects.all().order_by('tag')
    serializer_class = TagRestSerializer
