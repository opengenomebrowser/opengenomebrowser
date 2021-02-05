from django.shortcuts import render
from website.views.helpers.magic_string import MagicQueryManager
from website.views.helpers.extract_requests import contains_data, extract_data
from OpenGenomeBrowser.settings import ORTHOFINDER_ENABLED


def trees(request):
    context = dict(title='Trees')
    context['ORTHOFINDER_ENABLED'] = ORTHOFINDER_ENABLED
    context['genomes'] = []
    context['genome_to_species'] = dict()

    if contains_data(request, 'genomes'):
        qs = extract_data(request, 'genomes', list=True)

        try:
            magic_query_manager = MagicQueryManager(queries=qs)
            context['magic_query_manager'] = magic_query_manager
            context['genome_to_species'] = magic_query_manager.genome_to_species()
            context['can_calculate_trees'] = len(magic_query_manager.all_genomes) >= 3
        except Exception as e:
            context['error_danger'] = str(e)

    return render(request, 'website/trees.html', context)
