from django.shortcuts import render
from website.views.helpers.magic_string import MagicQueryManager


def trees(request):
    context = dict(title='Trees')

    context['genomes'] = []
    context['genome_to_species'] = dict()

    if 'genomes' in request.GET:
        qs = set(request.GET['genomes'].split(' '))

        try:
            magic_query_manager = MagicQueryManager(queries=qs)
            context['genomes'] = magic_query_manager.all_genomes
            context['genome_to_species'] = magic_query_manager.genome_to_species()
        except Exception as e:
            context['error_danger'] = str(e)

    context['can_calculate_trees'] = len(context['genomes']) >= 3

    return render(request, 'website/trees.html', context)
