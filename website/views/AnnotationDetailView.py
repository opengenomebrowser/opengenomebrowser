from website.models import Genome, Gene, Annotation
from django.views.generic import DetailView


class AnnotationDetailView(DetailView):
    model = Annotation
    slug_field = 'name'
    template_name = 'website/annotation_detail.html'
    context_object_name = 'annotation'

    def get_context_data(self, **kwargs):
        context = super(AnnotationDetailView, self).get_context_data(**kwargs)

        a: Annotation = self.object

        context['title'] = a.name

        genes = a.gene_set.all().order_by('identifier')[:2000].prefetch_related('genome__member__strain__taxid')

        context['capped'] = len(genes) == 2000

        genome_to_gene = {}
        for gene in genes:
            if gene.genome not in genome_to_gene:
                genome_to_gene[gene.genome] = [gene]
            else:
                genome_to_gene[(gene.genome)].append(gene)

        context['genome_to_gene'] = genome_to_gene

        return context
