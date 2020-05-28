from website.models import Gene
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

        # Convert sequences to HTML for colorization. See also stylesheet 'sequence-viewer.css'
        context['fasta_nucleotide'] = ''.join([F'<b class="{x}">{x}</b>' for x in g.fasta_nucleotide()])

        if g.fasta_protein():
            context['fasta_protein'] = ''.join([F'<b class="{x}">{x}</b>' for x in g.fasta_protein()])
        else:
            context['fasta_protein'] = '-- no protein sequence --'

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
