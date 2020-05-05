from website.models import Member
from website.models.TaxID import TaxID
from django.views.generic import DetailView


class MemberDetailView(DetailView):
    model = Member
    slug_field = 'identifier'
    template_name = 'website/member_detail.html'
    context_object_name = 'member'

    @staticmethod
    def __verbose(attr: str):
        if attr == 'is_representative': return 'Representative?'
        return Member._meta.get_field(attr).verbose_name

    def get_context_data(self, **kwargs):
        context = super(MemberDetailView, self).get_context_data(**kwargs)

        m: Member = self.object

        key_parameters = ['is_representative', 'contaminated', 'isolation_date', 'growth_condition',
                          'geographical_coordinates', 'geographical_name']
        context['key_parameters'] = [[self.__verbose(attr), getattr(m, attr)] for attr in key_parameters]

        seq_parameters = ['sequencing_tech', 'sequencing_tech_version', 'sequencing_date', 'sequencing_coverage']
        context['seq_parameters'] = [[self.__verbose(attr), getattr(m, attr)] for attr in seq_parameters]

        ass_parameters = ['assembly_tool', 'assembly_version', 'assembly_date', 'assembly_longest_scf', 'assembly_size',
                          'assembly_nr_scaffolds', 'assembly_n50', 'nr_replicons']
        context['ass_parameters'] = [[self.__verbose(attr), getattr(m, attr)] for attr in ass_parameters]

        ann_parameters = ['cds_tool', 'cds_tool_date', 'cds_tool_version']
        context['ann_parameters'] = [[self.__verbose(attr), getattr(m, attr)] for attr in ann_parameters]

        # origin of sequences
        if m.origin_excluded_sequences:
            sorted_list = sorted(m.origin_excluded_sequences, key=lambda entry: entry['percentage'], reverse=True)
            context['excluded_sequences'] = [(entry['taxid'],
                                              TaxID.get_or_create(taxid=entry['taxid']).taxscientificname,
                                              TaxID.get_or_create(taxid=entry['taxid']).color,
                                              entry['percentage'])
                                             for entry in sorted_list]
        if m.origin_included_sequences:
            sorted_list = sorted(m.origin_included_sequences, key=lambda entry: entry['percentage'], reverse=True)
            context['included_sequences'] = [(entry['taxid'],
                                              TaxID.get_or_create(taxid=entry['taxid']).taxscientificname,
                                              TaxID.get_or_create(taxid=entry['taxid']).color,
                                              entry['percentage'])
                                             for entry in sorted_list]

        return context
