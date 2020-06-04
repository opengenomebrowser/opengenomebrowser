from website.models import Gene, Annotation
from django.views.generic import DetailView
import re


class GeneDetailView(DetailView):
    model = Gene
    slug_field = 'identifier'
    template_name = 'website/gene_detail.html'
    context_object_name = 'gene'

    def get_context_data(self, **kwargs):
        context = super(GeneDetailView, self).get_context_data(**kwargs)

        g: Gene = self.object

        context['title'] = g.identifier

        # Convert sequences to HTML for colorization. See also stylesheet 'sequence-viewer.css'
        context['fasta_nucleotide'] = ''.join([F'<b class="{x}">{x}</b>' for x in g.fasta_nucleotide()])

        if g.fasta_protein():
            context['fasta_protein'] = ''.join([F'<b class="{x}">{x}</b>' for x in g.fasta_protein()])
        else:
            context['fasta_protein'] = '-- no protein sequence --'

        annotations = g.annotations.order_by('name').reverse()  # reverse because interesting GO-terms tend to have high values

        annotations = {anno_type: annotations.filter(anno_type=anno_type) for anno_type in Annotation.AnnotationTypes}

        annotations = {anno_type: annos for anno_type, annos in annotations.items() if len(annos) > 0}

        context['annotations'] = annotations

        # Find previous and next gene
        match = re.search('\d+$', g.identifier)
        if match:
            current_str = match.group(0)
            current = int(current_str)
            next = current + 1
            previous = current - 1

            prefix = g.identifier[0:-len(current_str)]
            formatter = '{:0' + str(len(current_str)) + 'd}'

            next = prefix + formatter.format(next)
            prev = prefix + formatter.format(previous)

            print(next, prev)
            if Gene.objects.filter(identifier=next).exists():
                context['next_gene'] = next
            if Gene.objects.filter(identifier=prev).exists():
                context['prev_gene'] = prev

        return context
