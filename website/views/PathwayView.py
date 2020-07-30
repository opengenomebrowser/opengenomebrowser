from django.shortcuts import render
from website.models.PathwayMap import PathwayMap
from website.models.Genome import Genome
from OpenGenomeBrowser import settings

type_dict = PathwayMap._get_type_dict()


def pathway_view(request):
    context = {}

    map: PathwayMap = None
    found_genomes: [Genome] = None
    map_is_valid = False
    genomes_are_valid = False

    context['type_dict'] = type_dict
    context['PATHWAY_MAPS_RELATIVE'] = settings.PATHWAY_MAPS_RELATIVE

    if 'map' in request.GET:
        map_slug = request.GET['map']
        try:
            map = PathwayMap.objects.get(slug=map_slug)
            context['map'] = map
            map_is_valid = True
        except PathwayMap.DoesNotExist:
            context['error_danger'] = F'Could not find map by slug: {map_slug}.'

    if 'genomes' in request.GET:
        query_genomes = set(request.GET['genomes'].split(' '))
        found_genomes = Genome.objects.filter(identifier__in=query_genomes)

        if len(query_genomes) == len(found_genomes):
            context['genomes'] = found_genomes
            context['genome_to_species'] = {genome.identifier: genome.taxscientificname for genome in found_genomes}
            genomes_are_valid = True
        else:
            found_genomes = set(found_genomes.values_list('identifier', flat=True))
            context['error_danger'] = F'Could not find {query_genomes.symmetric_difference(found_genomes)}.'

    if map_is_valid and genomes_are_valid:
        context['strains'] = {genome.identifier: list(map.annotations.filter(genomecontent__genome=genome).values_list(flat=True))
                              for genome in found_genomes}

    return render(request, 'website/pathway.html', context)
