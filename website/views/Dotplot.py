from django.shortcuts import render
from django.http import JsonResponse
from lib.dot.dot_prep_wrapper import DotPrep
from website.models.Genome import Genome
from plugins import calculate_dotplot


def dotplot_view(request):
    context = dict(
        title='Dotplot',
        error_danger=[], error_warning=[], error_info=[]
    )

    for ref_or_query in ['ref', 'query']:
        identifier = request.GET.get(ref_or_query, None)
        if identifier:
            try:
                context[f'genome_{ref_or_query}'] = Genome.objects.get(identifier=identifier)
            except Genome.DoesNotExist:
                context['error_danger'].append(f'Could not find {ref_or_query} genome: {identifier}')

    mincluster = request.GET.get('mincluster', 65)
    if str(mincluster).isdigit():
        context['mincluster'] = int(mincluster)
    else:
        context['mincluster'] = 65
        context['error_danger'].append(f'mincluster must be numeric: {mincluster}')

    return render(request, 'website/dotplot.html', context)


def get_dotplot_annotations(request):
    identifier = request.POST.get('identifier')
    is_ref = request.POST.get('is_ref') == 'true'

    genome = Genome.objects.get(identifier=identifier)

    if is_ref:
        annotations = DotPrep.gbk_to_annotation(genome.cds_gbk(relative=False), is_ref=is_ref)
    else:
        annotations = DotPrep.gbk_to_annotation(genome.cds_gbk(relative=False), is_ref=is_ref)

    return JsonResponse(dict(
        genome=identifier,
        is_ref=is_ref,
        annotations=annotations
    ))


def get_dotplot(request):
    """
    Get coords and index for Dot
    https://github.com/marianattestad/dot
    """
    identifier_ref = request.POST.get('identifier_ref')
    identifier_query = request.POST.get('identifier_query')
    mincluster = int(request.POST.get('mincluster'))

    genome_ref = Genome.objects.get(identifier=identifier_ref)
    genome_query = Genome.objects.get(identifier=identifier_query)

    fasta_ref = genome_ref.assembly_fasta(relative=True)
    fasta_query = genome_query.assembly_fasta(relative=True)

    coords, index = calculate_dotplot(fasta_ref=fasta_ref, fasta_qry=fasta_query, mincluster=mincluster)

    return JsonResponse(dict(
        coords=coords,
        coords_index=index
    ))
