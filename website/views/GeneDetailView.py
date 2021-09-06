import re
from django.views.generic import DetailView
from lib.subcellular_locations.go_to_sl import get_locusterms, LocationTerm
from website.models import Gene, Annotation, annotation_types

_locusterms = get_locusterms()
go_to_locusterm = {lt.go: lt.sl_id for lt in _locusterms}


class GeneDetailView(DetailView):
    model = Gene
    slug_field = 'identifier'
    template_name = 'website/gene_detail.html'
    context_object_name = 'gene'

    def get_context_data(self, **kwargs):
        context = super(GeneDetailView, self).get_context_data(**kwargs)

        g: Gene = self.object

        context['title'] = g.identifier
        context['error_danger'] = []
        context['taxid'] = g.genomecontent.taxid.id

        # Convert sequences to HTML for colorization. See also stylesheet 'sequence-viewer.css'
        context['fasta_nucleotide'] = ''.join([f'<b class="{x}">{x}</b>' for x in g.nucleotide_sequence()])

        if g.protein_sequence():
            context['fasta_protein'] = ''.join([f'<b class="{x}">{x}</b>' for x in g.protein_sequence()])
        else:
            context['fasta_protein'] = '-- no protein sequence --'

        annotations = g.annotations.order_by('name').reverse()  # reverse because interesting GO-terms tend to have high values

        annotations = {at.anno_type: annotations.filter(anno_type=at.anno_type) for at in annotation_types.values()}

        # remove empty categories
        annotations = {anno_type: annos for anno_type, annos in annotations.items() if len(annos) > 0}

        context['annotations'] = annotations

        # get uniprot subcellular location ids from GO-terms and SL-annotations
        sls: [(str, Annotation)] = []
        if 'GO' in annotations:
            locus_gos = annotations['GO'].filter(name__in=go_to_locusterm.keys())
            sls += [(go_to_locusterm[go.name], go) for go in locus_gos]
        if 'SL' in annotations:
            sls += [(sl.name[-4:], sl) for sl in annotations['SL']]
        if sls:
            context['sls'] = sls
            context['sls_ids'] = {sl for sl, anno in sls}

        # get scaffold id
        context['scaffold_id'] = g.get_gbk_seqrecord().scf_id

        # Find previous and next gene
        match = re.search('\d+$', g.identifier)
        if match:
            current_str = match.group(0)
            current = int(current_str)
            next_ = current + 1
            previous = current - 1

            prefix = g.identifier[0:-len(current_str)]
            formatter = '{:0' + str(len(current_str)) + 'd}'

            next_ = prefix + formatter.format(next_)
            prev = prefix + formatter.format(previous)

            if Gene.objects.filter(identifier=next_).exists():
                context['next_gene'] = next_
            if Gene.objects.filter(identifier=prev).exists():
                context['prev_gene'] = prev

        return context
