from website.models import Annotation
from django.views.generic import DetailView


class AnnotationDetailView(DetailView):
    model = Annotation
    slug_field = 'name'
    template_name = 'website/annotation_detail.html'
    context_object_name = 'annotation'

    def get_context_data(self, **kwargs):
        context = super(AnnotationDetailView, self).get_context_data(**kwargs)
        context['no_help'] = True

        a: Annotation = self.object

        context['title'] = a.name

        genes = a.gene_set.all().order_by('identifier')[:2000].prefetch_related('genomecontent__genome__organism__taxid')

        context['capped'] = len(genes) == 2000

        genomecontent_to_gene = {}
        for gene in genes:
            if gene.genomecontent not in genomecontent_to_gene:
                genomecontent_to_gene[gene.genomecontent] = [gene]
            else:
                genomecontent_to_gene[(gene.genomecontent)].append(gene)

        context['genome_to_gene'] = genomecontent_to_gene

        return context
