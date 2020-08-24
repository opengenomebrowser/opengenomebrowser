from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Q

from website.models import Annotation, Genome, Gene


class CompareGenes:
    @staticmethod
    def compare(request):
        context = dict(title='Compare Genes')

        if 'annotations' in request.GET or 'genomes' in request.GET:
            if not 'annotations' in request.GET and 'genomes' in request.GET:
                return HttpResponse(F'annotations and genes only work together. Got: {request.GET.keys()}', status=400)
            annotations = [a.replace('!!!', ' ') for a in request.GET['annotations'].split(' ')]
            genomes = request.GET['genomes'].split(' ')

            print(annotations, genomes)

            if 'genes' in request.GET:
                gene_ids = request.GET['genes'].split(' ')
                overlap_genes = Gene.objects.filter(
                    Q(identifier__in=gene_ids),
                    Q(genomecontent__in=genomes) & Q(annotations__in=annotations)
                )
            else:
                overlap_genes = Gene.objects.filter(
                    Q(genomecontent__in=genomes) & Q(annotations__in=annotations)
                )

            overlap_genes_string = '+'.join(overlap_genes.values_list('identifier', flat=True))
            return redirect(F"/compare-genes/?genes={overlap_genes_string}")

        if 'genes' in request.GET:
            gene_ids = request.GET['genes'].split(' ')
        else:
            gene_ids = []

        n_genes = len(gene_ids)

        context['n_genes'] = n_genes

        capping = 20

        if n_genes <= capping:
            context['key_genes'] = gene_ids
        else:
            context['key_genes'] = gene_ids[:capping]
            context['error_warning'] = F'{n_genes} genes were capped at {capping}'

        return render(request, 'website/compare_genes.html', context)
