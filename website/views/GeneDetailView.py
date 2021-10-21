import re
from django.views.generic import DetailView
from lib.subcellular_locations.go_to_sl import get_locusterms
from website.models import Gene, PathwayMap, Annotation, annotation_types

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

        # find annoations; reverse because interesting GO-terms tend to have high values
        context['annotations'] = g.annotations.order_by('-name', 'anno_type').prefetch_related('pathwaymap_set').all()

        # find relevant pathways
        context['pathways'] = PathwayMap.objects.filter(annotations__in=g.annotations.all()).distinct().order_by('slug')

        # get uniprot subcellular location ids from GO-terms and SL-annotations
        gos = g.annotations.filter(anno_type='GO', name__in=go_to_locusterm.keys())
        sls = g.annotations.filter(anno_type='SL')
        location_annotations = []
        if gos.exists():
            location_annotations += [('SL-' + go_to_locusterm[go.name], go) for go in gos]
        if sls.exists():
            location_annotations += [(sl.name, sl) for sl in sls]
        context['location_annotations'] = location_annotations
        context['sls_ids'] = {sl[-4:] for sl, anno in location_annotations}

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
