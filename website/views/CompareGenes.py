from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Q

from OpenGenomeBrowser.settings import DEFAULT_ANNOTATION_TYPE
from website.models import annotation_types, Gene
from website.views.Api import err
from website.views.helpers.extract_errors import extract_errors
from website.views.helpers.extract_requests import contains_data, extract_data, extract_data_or


class CompareGenes:
    @staticmethod
    def compare(request):
        context = extract_errors(request, dict(title='Compare Genes'))

        context['anno_types'] = annotation_types.values()
        context['default_anno_type'] = extract_data_or(request, 'anno_type', default=DEFAULT_ANNOTATION_TYPE)
        print(context['default_anno_type'], DEFAULT_ANNOTATION_TYPE)

        # Get genes
        if contains_data(request, 'genes'):
            gene_ids = extract_data(request, 'genes', list=True)
        else:
            gene_ids = []

        genes = Gene.objects.filter(identifier__in=gene_ids)
        if not len(set(gene_ids)) == len(genes):
            return err(F"{len(set(gene_ids))} were submitted but only {len(genes)} genes were found.")

        # If annotations and genomes in query: find genes and union queryset
        if contains_data(request, 'annotations') or contains_data(request, 'genomes'):
            if not contains_data(request, 'annotations') and contains_data(request, 'genomes'):
                return HttpResponse(f'annotations and genomes only work together. Got: {request.GET.keys()}', status=400)
            annotations = extract_data(request, 'annotations', list=True)
            genomes = extract_data(request, 'genomes', list=True)

            overlap_genes = Gene.objects.filter(
                Q(genomecontent__in=genomes) & Q(annotations__in=annotations)
            )

            genes = genes.union(overlap_genes)

        n_genes = len(genes)

        context['genes'] = genes
        context['n_genes'] = n_genes

        if n_genes > 20:
            context['error_warning'].append(f'Queries with {n_genes} genes may be slow - consider comparing fewer.')

        return render(request, 'website/compare_genes.html', context)
