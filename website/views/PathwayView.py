from django.shortcuts import render
from website.models.PathwayMap import PathwayMap
from OpenGenomeBrowser import settings
from website.views.helpers.magic_string import MagicQueryManager, MagicError
from website.views.helpers.extract_requests import contains_data, extract_data
from collections import Counter
from django.db.models import Q, Count

type_dict = PathwayMap._get_type_dict()


def pathway_view(request):
    context = dict(title='Pathways', error_danger=[], error_warning=[])

    map: PathwayMap = None
    map_is_valid = False

    context['type_dict'] = type_dict
    context['PATHWAY_MAPS_RELATIVE'] = settings.PATHWAY_MAPS_RELATIVE
    context['genome_to_species'] = '{}'

    if contains_data(request, key='map'):
        map_slug = extract_data(request, key='map')
        try:
            map = PathwayMap.objects.get(slug=map_slug)
            context['map'] = map
            map_is_valid = True
        except PathwayMap.DoesNotExist:
            context['error_danger'].append(F'Could not find map by slug: {map_slug}.')

    magic_query_managers = []
    genome_to_species = {}

    groups_of_genomes = {}
    i = 1
    while contains_data(request, key=f'g{i}'):
        try:
            group_id = f'g{i}'
            qs = set(extract_data(request, key=group_id, list=True))
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
        except Exception:
            context['error_danger'].append(F'Failed to extract genomes from group {i}.')
            groups_of_genomes = {}
            break

    context['groups_of_genomes'] = groups_of_genomes

    context['magic_query_managers'] = magic_query_managers
    context['initial_queries'] = [list(m.queries) for m in magic_query_managers]

    context['genome_to_species'] = genome_to_species

    return render(request, 'website/pathway.html', context)


def score_pathway_maps(request):
    from django.contrib.postgres.aggregates.general import ArrayAgg
    from django.http import JsonResponse

    group_ids = []
    groups_of_genomes = {}

    i = 1
    while f'g{i}[]' in request.POST:
        group_ids.append(f'g{i}[]')
        i += 1

    for group_id in group_ids:
        try:
            qs = set(request.POST.getlist(group_id))
            magic_query_manager = MagicQueryManager(queries=qs)
        except Exception as e:
            return JsonResponse(dict(success='false', result=e.message))

        identifiers = list(magic_query_manager.all_genomes.values_list('identifier', flat=True))
        assert len(identifiers) > 0, f'Group g{i} contains no genomes!'
        groups_of_genomes[group_id] = identifiers

    if len(groups_of_genomes) == 0:
        res = [dict(slug=m.slug, title=m.title, score='none') for m in PathwayMap.objects.all()]
        message = 'No genomes selected: show all pathways'
    else:
        qs = PathwayMap.objects \
            .annotate(n_annos=Count('annotations'))
        for group_id, genomes in groups_of_genomes.items():
            qs = qs.annotate(**{group_id: ArrayAgg('annotations', filter=Q(annotations__genomecontent__in=genomes))})

        if len(groups_of_genomes) == 1:
            fn = get_score_one
            message = 'One group: most covered pathways first'
        else:
            fn = get_score_many
            message = f'{len(groups_of_genomes)} groups: most different pathways first'

        res = [dict(slug=m.slug, title=m.title, score=fn(m, groups_of_genomes)) for m in qs.all()]
        res = sorted(res, key=lambda k: k['score'], reverse=True)

    return JsonResponse(dict(success='true', result=res, message=message))


def get_score_one(map: PathwayMap, groups_of_genomes) -> float:
    """
    :param map: PathwayMap, annotated with g{i} and n_annos
    :param groups_of_genomes: dict of list of identifiers ({g1: [identifier, identifier, ...], g2: [...])
    :return: float: how covered the pathway is
    """
    grp_id = list(groups_of_genomes.keys())[0]
    anno_to_count = Counter(getattr(map, grp_id))
    score = sum(anno_to_count.values()) / len(groups_of_genomes[grp_id]) / map.n_annos
    return round(score, 10)


def get_score_many(map: PathwayMap, groups_of_genomes) -> float:
    """
    :param map: PathwayMap, annotated with g{i} and n_annos
    :param groups_of_genomes: dict of list of identifiers ({g1: [identifier, identifier, ...], g2: [...])
    :return: float: the more different the groups are with regards to the pathway, the higher the score
    """
    keys = set()
    counters = []
    group_lenths = []
    for i, genomes in enumerate(groups_of_genomes, 1):
        group_lenths.append(len(genomes))
        anno_to_count = Counter(getattr(map, f'g{i}[]'))
        counters.append(anno_to_count)
        keys = keys.union(set(anno_to_count.keys()))

    score = 0.0
    for key in keys:
        rel_have = [c.get(key, 0) / n for c, n in zip(counters, group_lenths)]
        score += max(rel_have) - min(rel_have)

    return round(score / map.n_annos, 10)
