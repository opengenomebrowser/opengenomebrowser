from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Q

from website.models import Annotation, Genome, Gene
from website.views.Api import err


class CompareGenes:
    @staticmethod
    def compare(request):
        context = dict(title='Compare Genes')

        context['anno_types'] = Annotation.AnnotationTypes

        # If annotations and genomes in query: find genes and redirect to here.
        if 'annotations' in request.GET or 'genomes' in request.GET:
            if not 'annotations' in request.GET and 'genomes' in request.GET:
                return HttpResponse(F'annotations and genomes only work together. Got: {request.GET.keys()}', status=400)
            annotations = [a.replace('!!!', ' ') for a in request.GET['annotations'].split(' ')]
            genomes = request.GET['genomes'].split(' ')

            print(annotations, genomes)

            # GENOMES, ANNOTATIONS AND GENES
            if 'genes' in request.GET:
                gene_ids = request.GET['genes'].split(' ')
                overlap_genes = Gene.objects.filter(
                    Q(identifier__in=gene_ids),
                    Q(genomecontent__in=genomes) & Q(annotations__in=annotations)
                )
            else:
                # GENOMES AND ANNOTATIONS
                overlap_genes = Gene.objects.filter(
                    Q(genomecontent__in=genomes) & Q(annotations__in=annotations)
                )

            overlap_genes_string = '+'.join(overlap_genes.values_list('identifier', flat=True))
            return redirect(F"/compare-genes/?genes={overlap_genes_string}")

        # If only genes in request
        if 'genes' in request.GET:
            gene_ids = request.GET['genes'].split(' ')
        else:
            gene_ids = []

        genes = Gene.objects.filter(identifier__in=gene_ids)
        if not len(set(gene_ids)) == len(genes):
            return err(F"{len(set(gene_ids))} were submitted but only {len(genes)} genes were found.")

        n_genes = len(genes)

        context['genes'] = genes
        context['n_genes'] = n_genes

        if n_genes > 20:
            context['error_warning'] = F'Queries with {n_genes} genes may be slow - consider comparing fewer.'

        return render(request, 'website/compare_genes.html', context)
