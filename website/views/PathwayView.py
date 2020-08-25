from django.shortcuts import render
from website.models.PathwayMap import PathwayMap
from website.models.Genome import Genome
from website.models.TaxID import TaxID
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

        genome_identifiers, magic_words = set(), set()
        for q in qs:
            if q.startswith('@'):
                magic_words.add(q)
            else:
                genome_identifiers.add(q)

        found_genomes = Genome.objects.filter(identifier__in=genome_identifiers)

        if len(genome_identifiers) == len(found_genomes):
            genomes_are_valid = True
        else:
            found_genomes = set(found_genomes.values_list('identifier', flat=True))
            context['error_danger'] = F'Could not find {genome_identifiers.symmetric_difference(found_genomes)}.'

        for magic_string in magic_words:
            magic_word, query = magic_string[1:].split(':', maxsplit=1)
            taxid = TaxID.objects.filter(taxscientificname=query)
            if not taxid.exists():
                context['error_danger'] = F'Could not interpret magic word: {magic_string}.'
            else:
                taxid: TaxID = taxid[0]
                magic_genomes = taxid.get_child_genomes(representatives_only=True)

                # add to found_genomes
                found_genomes = found_genomes.union(magic_genomes)

    print(len(found_genomes), found_genomes)
    context['genomes'] = found_genomes
    context['genome_to_species'] = {genome.identifier: genome.taxscientificname for genome in found_genomes}

    if map_is_valid and genomes_are_valid:
        context['strains'] = {genome.identifier: list(map.annotations.filter(genomecontent__genome=genome).values_list(flat=True))
                              for genome in found_genomes}

    return render(request, 'website/pathway.html', context)
