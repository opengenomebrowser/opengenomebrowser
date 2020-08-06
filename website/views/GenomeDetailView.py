from website.models import Genome
from website.models.TaxID import TaxID
from django.views.generic import DetailView
from lib.get_tax_info.get_tax_info import TaxID as RawTaxID
from math import sqrt
import numpy as np
import pandas as pd


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
        context['genome'] = g

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
            context['excluded_sequences'] = [create_entry(entry['taxid'], entry['percentage'])
                                             for entry in sorted_list]
        if g.origin_included_sequences:
            sorted_list = sorted(g.origin_included_sequences, key=lambda entry: entry['percentage'], reverse=True)
            context['included_sequences'] = [create_entry(entry['taxid'], entry['percentage'])
                                             for entry in sorted_list]

        if g.sixteen_s and len(g.sixteen_s) > 0:
            context['sixteen_s'] = {db_name: covert_sixteen_s(data) for db_name, data in g.sixteen_s.items()}

        return context


def covert_sixteen_s(data: dict):
    df = pd.DataFrame(data)
    df.set_index('taxid', inplace=True)
    df.index.name = None

    df['species'] = [create_html_entry(taxid)[1] for taxid in df.index]

    if 'evalue' in df.columns:
        val_colname = 'evalue'
    else:
        assert 'confidence' in df.columns
        val_colname = 'confidence'

    df = df[['species', 'description', val_colname]]

    df.columns = df.columns.str.capitalize()
    html = df.to_html(escape=False, index=False)

    html = html \
        .replace('border="1" class="dataframe"',
                 F'id="{id}" class="table table-bordered table-sm white-links"', 1) \
        .replace('<thead>', '<thead class="thead-dark">', 1) \
        .replace('<th>g', '<th scope="col">g', len(df.columns))

    return html


def create_html_entry(taxid: int):
    try:
        t = TaxID.objects.get(id=taxid)
        color = t.color
        sci_name = t.taxscientificname
        html = t.html
    except TaxID.DoesNotExist:
        t = RawTaxID(taxid=taxid)
        color = tuple(np.random.randint(256, size=3))  # random color
        sci_name = t.scientific_name
        html = F"""<div class="ogb-tag" style="background-color:rgb{color}; color:{'white' if is_text_color_white(color) else 'black'}">{sci_name} (taxid {taxid})</div>"""
    return taxid, html, sci_name, color


def create_entry(taxid: int, percentage: float):
    taxid, html, sci_name, color = create_html_entry(taxid)
    return taxid, html, sci_name, color, percentage


def is_text_color_white(color: (int, int, int)) -> bool:
    r, g, b = color
    luminance = sqrt(0.299 * (r ** 2) + 0.587 * (g ** 2) + 0.114 * (b ** 2))
    return True if luminance < 160 else False
