from website.models import Genome
from website.models.TaxID import TaxID
from django.views.generic import DetailView
from django.template import engines
from math import sqrt
import numpy as np
import pandas as pd

from lib.get_tax_info.get_tax_info import GetTaxInfo
from lib.get_tax_info.get_tax_info import TaxID as RawTaxID

RawTaxID.gti = GetTaxInfo()


class ParameterField:
    template = engines['django'].from_string('''
<tr>
    <th scope="row">{{ param.verbose }}</th>
    {% if param.url %}
        <td><a href="{{ param.url }}">{{ param.value }}</a></td>
    {% else %}
        <td>{{ param.value }}</td>
    {% endif %}
</tr>''')
    env_template = engines['django'].from_string('''
<tr>
    <th scope="row">{{ param.verbose }}</th>
    <td>
    {% for value, url_value in param.list_values %}
        <a class="badge badge-warning" href="https://www.ebi.ac.uk/ols/ontologies/envo/terms?iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2F{{ url_value }}">{{ value }}</a>
    {% endfor %}
    </td>
</tr>''')
    ref_template = engines['django'].from_string('''
<tr>
    <th scope="row">{{ param.verbose }}</th>
    <td>
    {% for ref in param.value %}
        <a class="badge badge-info" href="{{ ref.url }}">{{ ref.name }}</a>
    {% endfor %}
    </td>
</tr>''')

    def __init__(self, genome: Genome, attr: str):
        self.genome = genome
        self.attr = attr
        self.value = getattr(genome, attr)
        if self.value == []: self.value = None

    @property
    def verbose(self):
        if self.attr == 'is_representative': return 'Representative?'
        return Genome._meta.get_field(self.attr).verbose_name

    @property
    def url(self):
        if self.attr == 'bioproject_accession': return f'https://www.ncbi.nlm.nih.gov/bioproject/?term={self.value}'
        if self.attr == 'biosample_accession': return f'https://www.ncbi.nlm.nih.gov/biosample/?term={self.value}'
        if self.attr == 'genome_accession': return f'https://www.ncbi.nlm.nih.gov/nuccore/{self.value}'
        return None

    def list_values(self):
        return [(v, v.replace(':', '_')) for v in self.value]

    def html(self):
        if self.attr.startswith('env_'):
            return self.env_template.render({'param': self})  # environment
        if self.attr == 'literature_references':
            return self.ref_template.render({'param': self})  # reference
        else:
            return self.template.render({'param': self})


class GenomeDetailView(DetailView):
    model = Genome
    slug_field = 'identifier'
    template_name = 'website/genome_detail.html'
    context_object_name = 'genome'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        g: Genome = self.object

        context['admin_actions'] = [
            dict(url=f'/admin/website/genome/{g.pk}/change/', action='Edit genome'),
            dict(url=f'/admin/markdown-editor/?genome={g.identifier}', action='Edit genome markdown'),
            dict(url=f'/admin/markdown-editor/?organism={g.organism.name}', action='Edit organism markdown')
        ]

        context['genome'] = g

        context['title'] = g.identifier

        context['genome_markdown'] = g.markdown()
        context['organism_markdown'] = g.organism.markdown()

        key_parameters = ['is_representative', 'contaminated', 'isolation_date', 'growth_condition',
                          'geographical_coordinates', 'geographical_name',
                          'env_broad_scale', 'env_local_scale', 'env_medium',
                          'bioproject_accession', 'biosample_accession', 'genome_accession',
                          'literature_references']
        context['key_parameters'] = [ParameterField(genome=g, attr=attr) for attr in key_parameters]

        seq_parameters = ['library_preparation', 'sequencing_tech', 'sequencing_tech_version', 'sequencing_date', 'sequencing_coverage']
        context['seq_parameters'] = [ParameterField(genome=g, attr=attr) for attr in seq_parameters]

        ass_parameters = ['assembly_tool', 'assembly_version', 'assembly_date', 'assembly_gc', 'assembly_longest_scf', 'assembly_size',
                          'assembly_nr_scaffolds', 'assembly_n50', 'assembly_gaps', 'assembly_ncount', 'nr_replicons']
        context['ass_parameters'] = [ParameterField(genome=g, attr=attr) for attr in ass_parameters]

        ann_parameters = ['cds_tool', 'cds_tool_date', 'cds_tool_version']
        context['ann_parameters'] = [ParameterField(genome=g, attr=attr) for attr in ann_parameters]

        context['custom_tables'] = []
        if g.custom_tables:
            context['custom_tables'] = [
                (
                    title,
                    create_table(data, table_id=F'custom_table_{title}'),
                    data.get('pie_chart_col', None)
                )
                for title, data in g.custom_tables.items()]

        return context


def create_table(data: dict, table_id: str) -> str:
    try:
        df = pd.DataFrame(data['rows'])
        if 'columns' in data:
            df = df.reindex(data['columns'], axis=1)
        if 'index_col' in data:
            df.set_index(data['index_col'])
        for taxid_col in data.get('taxid_cols', []):
            df[taxid_col] = df[taxid_col].apply(taxid_to_html)
        html = dataframe_to_bootstrap_html(df, table_id)
    except Exception as e:
        import json, traceback
        traceback.print_exc()
        return f'''
        <div class="alert alert-danger" role="alert">
            Failed to parse custom table: {e}<br>
            Data: {json.dumps(data)}
        </div>'''
    return html


def dataframe_to_bootstrap_html(df: pd.DataFrame, table_id: str, index=False) -> str:
    html = df.to_html(escape=False, index=index, table_id=table_id)

    html = html \
        .replace('border="1" class="dataframe"',
                 F'class="table table-bordered table-sm white-links"', 1) \
        .replace('<thead>', '<thead class="thead-dark">', 1) \
        .replace('<th>g', '<th scope="col">g', len(df.columns)) \
        .replace('<tr style="text-align: right;">', '<tr>', 1)

    return html


def taxid_to_html(taxid: int):
    try:
        t = TaxID.objects.get(id=taxid)
        html = t.html
    except TaxID.DoesNotExist:
        t = RawTaxID(taxid=taxid)
        color = tuple(np.random.randint(256, size=3))  # random color
        html = F"""<div class="ogb-tag" style="background-color:rgb{color}; color:{'white' if is_text_color_white(color) else 'black'}">{t.scientific_name} (taxid {taxid})</div>"""
    return html


def is_text_color_white(color: (int, int, int)) -> bool:
    r, g, b = color
    luminance = sqrt(0.299 * (r ** 2) + 0.587 * (g ** 2) + 0.114 * (b ** 2))
    return True if luminance < 160 else False
