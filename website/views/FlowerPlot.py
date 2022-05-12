from io import StringIO

from django.db.models import Q
import pandas as pd
from django.db.models import Count
from django.shortcuts import render
from django.http import JsonResponse

from flower_plot import flower_plot

from website.views.helpers.extract_errors import extract_errors
from website.views.helpers.magic_string import MagicQueryManager
from website.views.helpers.extract_requests import contains_data, extract_data

from website.models import Genome, GenomeContent, Annotation
from website.models.Annotation import annotation_types, settings


def flower_view(request):
    """
    This function loads the page /flower-plot/

    :param request: may contain: ['g1[]', 'g2[]', 'anno_type']
    :returns: rendered flower_plot.html
    """

    context = extract_errors(request, dict(
        title='Flower plot',
        anno_types=annotation_types.values(),
        anno_type=settings.DEFAULT_ANNOTATION_TYPE,
        add_non_annotated=False
    ))

    if contains_data(request, 'anno_type'):
        context['anno_type'] = extract_data(request, 'anno_type')

    if contains_data(request, 'add_non_annotated'):
        context['add_non_annotated'] = extract_data(request, 'add_non_annotated').lower() == 'true'

    if contains_data(request, 'genomes'):
        genomes = extract_data(request, 'genomes', list=True)

        try:
            magic_query_manager = MagicQueryManager(queries=genomes)
            context['magic_query_manager'] = magic_query_manager
        except Exception as e:
            context['error_danger'].append(str(e))

    context['success'] = len(context['error_warning']) == 0

    return render(request, 'website/flower_plot.html', context)


def flower_svg(request):
    try:
        qs = set(request.POST.getlist('genomes[]'))
        anno_type = request.POST.get('anno_type')
        assert anno_type in annotation_types, f'anno_type is not in {annotation_types.keys()}'
        add_non_annotated = request.POST.get('add_non_annotated').lower() == 'true'
    except Exception as e:
        return JsonResponse(dict(success='false', message=f'Failed to extract genomes[] or anno_type. {e}'), status=500)
    try:
        genomes_to_taxname = {
            i: t
            for i, t in
            MagicQueryManager(qs, raise_errors=True)
                .all_genomes.values_list('identifier', 'organism__taxid__taxscientificname')
        }
        assert len(genomes_to_taxname) > 0, f'No genomes found'
    except Exception as e:
        return JsonResponse(dict(success='false', message=f'Magic query is bad: {e}'), status=500)

    genome_to_data, n_core = get_flower_data(genomes_to_taxname.keys(), anno_type, add_non_annotated)

    import matplotlib.pyplot as plt
    plt.close()
    ax = flower_plot(genome_to_data, n_core)
    plt.tight_layout()

    pipe = StringIO()
    plt.savefig(pipe, format='svg')
    svg = pipe.getvalue()

    return JsonResponse(dict(success='true', svg=svg, anno_type=anno_type, genomes_taxname=genomes_to_taxname))


def get_flower_data(genomes: [str], anno_type: str, add_non_annotated) -> (int, dict[str:int], dict[str:int]):
    """
    Calculate the number of core, shell and unique annotations

    :param genomes:
    :param anno_type:
    :param add_non_annotated:
    :return: n_core:int, n_unique:dict, n_shell:dict
    """
    genomes_qs = Genome.objects.filter(identifier__in=genomes)
    assert len(genomes) == genomes_qs.count(), f'Failed to find some genomes! {len(genomes)=} != {genomes_qs.count()=}'

    genome_to_color = dict(genomes_qs.values_list('identifier', 'organism__taxid__color'))

    annos_qs = Annotation.objects.filter(anno_type=anno_type, genomecontent__identifier__in=genomes)
    for g in genomes:
        annos_qs = annos_qs.annotate(**{g: Count('genomecontent', filter=Q(genomecontent__identifier=g))})
    annos_qs = annos_qs.values_list('name', *genomes)

    annos = pd.DataFrame(list(annos_qs), columns=['name', *genomes])
    annos.set_index('name', inplace=True)
    annos = annos.applymap(bool)

    total_annos = len(annos)
    n_total = annos.sum().to_dict()

    core_mask = annos.all(axis=1)  # core
    n_core = sum(core_mask)

    annos = annos[~core_mask]  # remove core

    unique_mask = annos.sum(axis=1) == 1
    unique = annos[unique_mask]
    genome_to_n_unique = unique.sum().to_dict()

    annos = annos[~unique_mask]  # remove singletons, we are left with shell annotations

    assert n_core + sum(genome_to_n_unique.values()) + len(annos) == total_annos

    genome_to_n_shell = annos.sum().to_dict()

    for g in genomes:
        assert n_core + genome_to_n_unique[g] + genome_to_n_shell[g] == n_total[g]

    if add_non_annotated:
        # add genes with no annotations
        n_annotated_genes = GenomeContent.objects.filter(
            identifier__in=genomes,
            gene__annotations__anno_type=anno_type
        ) \
            .values('identifier') \
            .annotate(total=Count('gene__identifier', distinct=True))
        n_annotated_genes = {e['identifier']: e['total'] for e in n_annotated_genes}
        n_genes = dict(GenomeContent.objects.filter(identifier__in=genomes).values_list('identifier', 'n_genes'))
        n_non_annotated = {genome: n_genes[genome] - n_annotated_genes.get(genome, 0) for genome in n_genes}

        genome_to_n_unique = {g: n + n_non_annotated[g] for g, n in genome_to_n_unique.items()}

    rgb_to_hsa = lambda rgb: tuple(int(c) / 256 for c in rgb.split(','))
    genome_to_data = {i: {
        'color': rgb_to_hsa(genome_to_color[i]),
        'shell': genome_to_n_shell[i],
        'unique': genome_to_n_unique[i],
    } for i in genomes}

    return genome_to_data, n_core
