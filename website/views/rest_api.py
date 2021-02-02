from rest_framework import viewsets, filters, mixins

from website.serializers.rest_serializers import *

default_field = {
    'organism': 'name',
    'genome': 'identifier',
    'taxid': 'taxscientificname',
    'tag': 'tag',
}


class DynamicSearchFilter(filters.SearchFilter):

    def get_search_fields(self, view, request):
        return request.GET.getlist('search_fields', [default_field[view.basename]])


class TaxIDViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for TaxIDs (read-only).
    """
    queryset = TaxID.objects.all().order_by('id')
    serializer_class = TaxIDRestSerializer
    filter_backends = (DynamicSearchFilter,)


class GenomeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Genomes (read-only).
    """
    queryset = Genome.objects.all().order_by('identifier')
    serializer_class = GenomesRestSerializer
    filter_backends = (DynamicSearchFilter,)
    lookup_field = 'identifier'
    lookup_value_regex = '[a-zA-Z0-9\.\-\_]{1,50}'


class OrganismViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Organisms (read-only).
    """
    queryset = Organism.objects.all().order_by('name')
    serializer_class = OrganismRestSerializer
    filter_backends = (DynamicSearchFilter,)
    lookup_field = 'name'


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Tags (read-only).
    """
    queryset = Tag.objects.all().order_by('tag')
    serializer_class = TagRestSerializer
    filter_backends = (DynamicSearchFilter,)
