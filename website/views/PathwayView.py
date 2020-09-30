from django.shortcuts import render
from website.models.PathwayMap import PathwayMap
from website.models.Genome import Genome
from website.models.TaxID import TaxID
from OpenGenomeBrowser import settings
from website.views.helpers.magic_string import MagicString

type_dict = PathwayMap._get_type_dict()


def pathway_view(request):
    context = dict(title='Pathways')

    map: PathwayMap = None
    map_is_valid = False
    genomes_are_valid = False

    context['type_dict'] = type_dict
    context['PATHWAY_MAPS_RELATIVE'] = settings.PATHWAY_MAPS_RELATIVE
    context['genome_to_species'] = '{}'

    if 'map' in request.GET:
        map_slug = request.GET['map']
        try:
            map = PathwayMap.objects.get(slug=map_slug)
            context['map'] = map
            map_is_valid = True
        except PathwayMap.DoesNotExist:
            context['error_danger'] = F'Could not find map by slug: {map_slug}.'

    if 'genomes' in request.GET:
        qs = set(request.GET['genomes'].split(' '))

        try:
            found_genomes = MagicString.get_genomes(queries=qs)
            context['genomes'] = found_genomes
            context['genome_to_species'] = {genome.identifier: genome.taxscientificname for genome in found_genomes}
            genomes_are_valid = True
        except ValueError as e:
            context['error_danger'] = str(e)

    if map_is_valid and genomes_are_valid:
        context['organism_to_annotations'] = {
            genome.identifier: list(map.annotations.filter(genomecontent__genome=genome).values_list(flat=True))
            for genome in found_genomes
        }

    return render(request, 'website/pathway.html', context)
