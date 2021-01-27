import json

from django.shortcuts import render
from website.models.PathwayMap import PathwayMap
from website.models.Genome import Genome
from website.models.TaxID import TaxID
from OpenGenomeBrowser import settings
from website.views.helpers.magic_string import MagicQueryManager

type_dict = PathwayMap._get_type_dict()



def pathway_view(request):
    context = dict(title='Pathways')

    map: PathwayMap = None
    map_is_valid = False

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

    magic_query_managers = []
    genome_to_species = {}
    try:
        groups_of_genomes = {}
        i = 1
        while f'g{i}' in request.GET:
            group_id = f'g{i}'
            qs = set(request.GET[group_id].split(' '))
            magic_query_manager = MagicQueryManager(queries=qs)
            magic_query_managers.append(magic_query_manager)
            genome_to_species.update(magic_query_manager.genome_to_species())

            if map_is_valid:
                organism_to_annotations = {
                    genome.identifier: list(map.annotations.filter(genomecontent__genome=genome).values_list(flat=True))
                    for genome in magic_query_manager.all_genomes
                }

                groups_of_genomes[f'g{i}'] = organism_to_annotations

            i += 1

        context['groups_of_genomes'] = groups_of_genomes

    except Exception as e:
        import traceback
        context['error_danger'] = F'Error: {e} :: {traceback.format_exc()}'

    context['magic_query_managers'] = magic_query_managers
    context['initial_queries'] = [list(m.queries) for m in magic_query_managers]

    context['genome_to_species'] = genome_to_species

    return render(request, 'website/pathway.html', context)
