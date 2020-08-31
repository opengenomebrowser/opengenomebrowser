from django.shortcuts import render
from website.views.helpers.magic_string import MagicString


def trees(request):
    context = dict(title='Trees')

    context['genomes'] = []
    context['genome_to_species'] = dict()

    if 'genomes' in request.GET:
        qs = set(request.GET['genomes'].split(' '))

        try:
            found_genomes = MagicString.get_genomes(queries=qs)
            context['genomes'] = found_genomes
            context['genome_to_species'] = {genome.identifier: genome.taxscientificname for genome in found_genomes}
        except ValueError as e:
            context['error_danger'] = str(e)

    context['can_calculate_trees'] = len(context['genomes']) >= 3

    return render(request, 'website/trees.html', context)
