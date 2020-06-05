from website.models import Genome
from website.models.TaxID import TaxID
from django.views.generic import DetailView


class GenomeDetailView(DetailView):
    model = Genome
    slug_field = 'identifier'
    template_name = 'website/genome_detail.html'
    context_object_name = 'genome'

    @staticmethod
    def __verbose(attr: str):
        if attr == 'is_representative': return 'Representative?'
        return Genome._meta.get_field(attr).verbose_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        g: Genome = self.object

        context['title'] = g.identifier

        key_parameters = ['is_representative', 'contaminated', 'isolation_date', 'growth_condition',
                          'geographical_coordinates', 'geographical_name']
        context['key_parameters'] = [[self.__verbose(attr), getattr(g, attr)] for attr in key_parameters]

        seq_parameters = ['sequencing_tech', 'sequencing_tech_version', 'sequencing_date', 'sequencing_coverage']
        context['seq_parameters'] = [[self.__verbose(attr), getattr(g, attr)] for attr in seq_parameters]

        ass_parameters = ['assembly_tool', 'assembly_version', 'assembly_date', 'assembly_longest_scf', 'assembly_size',
                          'assembly_nr_scaffolds', 'assembly_n50', 'nr_replicons']
        context['ass_parameters'] = [[self.__verbose(attr), getattr(g, attr)] for attr in ass_parameters]

        ann_parameters = ['cds_tool', 'cds_tool_date', 'cds_tool_version']
        context['ann_parameters'] = [[self.__verbose(attr), getattr(g, attr)] for attr in ann_parameters]

        # origin of sequences
        if g.origin_excluded_sequences:
            sorted_list = sorted(g.origin_excluded_sequences, key=lambda entry: entry['percentage'], reverse=True)
            context['excluded_sequences'] = [(entry['taxid'],
                                              TaxID.get_or_create(taxid=entry['taxid']).taxscientificname,
                                              TaxID.get_or_create(taxid=entry['taxid']).color,
                                              entry['percentage'])
                                             for entry in sorted_list]
        if g.origin_included_sequences:
            sorted_list = sorted(g.origin_included_sequences, key=lambda entry: entry['percentage'], reverse=True)
            context['included_sequences'] = [(entry['taxid'],
                                              TaxID.get_or_create(taxid=entry['taxid']).taxscientificname,
                                              TaxID.get_or_create(taxid=entry['taxid']).color,
                                              entry['percentage'])
                                             for entry in sorted_list]

        return context
