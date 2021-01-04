from django.shortcuts import render, HttpResponse
from django.db.models import Q, Count, Exists
from django.contrib.postgres.aggregates.general import ArrayAgg

import pandas as pd
import json

from website.models import Genome, Gene, GenomeContent
from website.models.Annotation import Annotation

from .GenomeDetailView import dataframe_to_bootstrap_html

from .helpers.magic_string import MagicQueryManager, MagicError


def annotation_view(request):
    context = dict(title='Annotation search')

    genomes_valid = False
    annotations_valid = False

    if 'genomes' in request.GET:
        qs = set(request.GET['genomes'].split(' '))

        try:
            magic_query_manager = MagicQueryManager(queries=qs)
            context['magic_query_manager'] = magic_query_manager
            context['genome_to_species'] = magic_query_manager.genome_to_species()
            genomes_valid = True
        except Exception as e:
            context['error_danger'] = str(e)

    if 'annotations' in request.GET:
        annotation_name_list = set(ann.replace('!!!', ' ') for ann in request.GET['annotations'].split(' '))
        annotations = Annotation.objects.filter(name__in=annotation_name_list)
        context['annotations'] = annotations
        if not len(annotation_name_list) == len(set(annotations.values_list('name', flat=True))):
            context['error_danger'] = F'Could not interpret these annotations: {annotation_name_list.symmetric_difference(annotations)}'
        else:
            annotations_valid = True

    if genomes_valid and annotations_valid:
        mm = MatrixMaker(magic_query_manager.all_genomes, annotations)

        group_to_table = mm.get_group_to_table()

        context.update(dict(
            matrix_header=mm.matrix.columns.to_list(),
            matrix_body=zip(mm.matrix.index, mm.matrix.values.tolist()),
            matrix_footer_covered=mm.matrix.sum().values.tolist(),
            matrix_footer_genomes=[len(g) for g in mm.grp_to_genomes.values()],
            matrix=mm.html_matrix,
            group_to_table=group_to_table
        ))

    return render(request, 'website/annotation_search.html', context)


def matrix(request):
    context = {}

    # check input
    if not 'genomes[]' and 'annotations[]' in request.POST:
        return HttpResponse('Request failed! Please POST genomes[] and annotations[].')

    qs = set(request.POST.getlist('genomes[]'))

    try:
        magic_query_manager = MagicQueryManager(qs)
    except Exception as e:
        return HttpResponse(F'Request failed: genomes[] incorrect. {e}')

    annotations = set(request.POST.getlist('annotations[]'))
    try:
        annotations = [Annotation.objects.get(name=anno.replace('!!!', ' ')) for anno in annotations]
    except Annotation.DoesNotExist:
        return HttpResponse('Request failed: annotations[] incorrect.')

    all_genomes = magic_query_manager.all_genomes

    mm = NewMatrixMaker(all_genomes, annotations)

    context = dict(
        matrix_header=mm.coverage_matrix.columns.to_list(),
        matrix_body=zip(mm.coverage_matrix.index, mm.coverage_matrix.values.tolist()),
        matrix_footer_covered=mm.coverage_matrix.sum().values.tolist(),
        matrix=mm.html_matrix
    )

    return render(request, 'website/annotation_search_matrix.html', context)


class NewMatrixMaker:
    def __init__(self, genomes: [Genome], annotations: [Annotation]):
        self.genomes = list(genomes)
        self.annotations = list(annotations)

        self.genome_to_html = {}  # cannot be done using list comprehension
        for genome in genomes:
            self.genome_to_html[genome.identifier] = genome.html

        self.annotation_to_html = {}  # cannot be done using list comprehension
        for annotation in annotations:
            self.annotation_to_html[annotation.name] = annotation.html

        self.coverage_matrix = self.__create_coverage_matrix()

        self.html_matrix = self.pandas_to_html(table=self.coverage_matrix, id='coverage-matrix')

    def __create_coverage_matrix(self):
        """
        use Postgres subqueries to efficiently calculate matrix
        """

        # create temporary column names without special symbols
        temp_name_to_annotation = [(f'matrix_anno_{i}', a) for i, a in enumerate([a.name for a in self.annotations])]

        # design query
        genomecontent_qs = GenomeContent.objects
        for temp_name, a in temp_name_to_annotation:
            genomecontent_qs = genomecontent_qs.annotate(**{temp_name: ArrayAgg('gene', filter=Q(gene__annotations__name=a))})
        genomecontent_qs = genomecontent_qs.filter(identifier__in=[g.identifier for g in self.genomes])

        matrix_values = genomecontent_qs.values_list(*['identifier'] + [temp_name for temp_name, a in temp_name_to_annotation])
        matrix = pd.DataFrame(matrix_values, columns=['identifier'] + [a for temp_name, a in temp_name_to_annotation])
        matrix.set_index('identifier', inplace=True)

        matrix = self.__sort_coverage_matrix(matrix)

        return matrix.T

    def __sort_coverage_matrix(self, matrix):
        def sort_by_pattern(row_or_col):
            return pattern_to_rank[tuple([bool(rc) for rc in row_or_col.values])]

        # sort by annotations by most prevalent
        pattern_to_rank = self.__pattern_to_rank(matrix, axis=1)
        matrix = matrix.reindex(matrix.apply(sort_by_pattern, axis=0).sort_values(ascending=False).index, axis=1)

        pattern_to_rank = self.__pattern_to_rank(matrix, axis=0)
        matrix = matrix.reindex(matrix.apply(sort_by_pattern, axis=1).sort_values(ascending=False).index, axis=0)

        return matrix

    def __pattern_to_rank(self, matrix, axis:int):
        # sort by most common pattern
        if axis == 0:
            patterns = list(set([tuple(row.values) for i, row in matrix.applymap(bool).iterrows()]))
        else:
            patterns = list(set([tuple(row.values) for i, row in matrix.applymap(bool).iteritems()]))
        patterns.sort()
        pattern_to_rank = {p: i for i, p in enumerate(patterns)}
        return pattern_to_rank

    def pandas_to_html(self, table: pd.DataFrame, id: str) -> str:
        tmp = table.__deepcopy__()
        tmp.columns = [self.genome_to_html[g] for g in tmp.columns]
        tmp.index = [self.annotation_to_html[a] for a in tmp.index]

        def cell_to_html(genes):
            n_genes = len(genes)
            if n_genes == 0:
                return F"<p style='color: lightgray' data-genes='{json.dumps(genes)}'>{n_genes}</p>"
            else:
                return F"<p data-genes='{json.dumps(genes)}'>{n_genes}</p>"

        tmp = tmp.applymap(cell_to_html)


        html = dataframe_to_bootstrap_html(tmp, table_id=id, index=True)

        return html


class MatrixMaker:
    def __init__(self, genomes: [Genome], annotations: [Annotation]):
        self.genomes = genomes

        self._genome_to_html = {}  # cannot be done using list comprehension
        for genome in genomes:
            self._genome_to_html[genome] = genome.html

        self.annotations = annotations

        self._annotation_to_html = {}  # cannot be done using list comprehension
        for annotation in annotations:
            self._annotation_to_html[annotation] = annotation.html

        self.matrix, \
        self.grp_to_genomes = self.__create_coverage_matrix()

        self.html_matrix = self.pandas_to_html(table=self.matrix, id='matrix-table')
        self.__add_footer()

    def pandas_to_html(self, table: pd.DataFrame, id: str) -> str:
        tmp = table.__deepcopy__()
        if type(tmp.columns[0]) == str:
            tmp.columns = [F'<a href="#header_{grp_id}">{grp_id}</a>' for grp_id in tmp.columns]
        else:
            tmp.columns = [self._genome_to_html[g] for g in tmp.columns]
        tmp.index = [self._annotation_to_html[a] for a in tmp.index]

        html = dataframe_to_bootstrap_html(tmp, table_id=id, index=True)

        return html

    def __add_footer(self):
        footer_covered = ''.join([F'<td>{s}</td>' for s in self.matrix.sum().values])
        footer_genomes = ''.join([F'<td>{len(g)}</td>' for g in self.grp_to_genomes.values()])

        self.html_matrix = self.html_matrix \
            .replace('      <td>True</td>', '      <td style="background-color: black">X</td>') \
            .replace('      <td>False</td>', '      <td></td>') \
            .replace('</tbody>',
                     F"""</tbody><tfoot class="table-dark text-light">
                    <tr><th scope="row">#covered</th>{footer_covered}</tr>
                    <tr><th scope="row">#genomes</th>{footer_genomes}</tr></tfoot>""", 1)

    @staticmethod
    def get_genes(annotation: Annotation, genomes: [Genome]) -> [Gene]:
        return annotation.gene_set.filter(genomecontent__genome__in=genomes).order_by('genomecontent__genome__identifier').prefetch_related(
            'genomecontent__genome__organism__taxid')

    def get_group_to_table(self) -> dict:
        return {grp_id: self.__create_group_table(grp_id, genomes) for grp_id, genomes in self.grp_to_genomes.items()}

    def __create_group_table(self, grp_id, genomes) -> str:
        genome_to_n_genes = dict()
        for genome in genomes:
            genome_to_n_genes[genome] = [self.__get_count_gene_tuple(genome, anno) for anno in self.matrix.index]
        table = pd.DataFrame(genome_to_n_genes)
        table.index = self.matrix.index

        # remove empty rows
        def tuple_sum(list_of_tuples):
            return sum(count for count, genes in list_of_tuples)

        table = table.loc[(table.apply(tuple_sum, axis=1) != 0),]

        # add genes to data-genes
        table = table.applymap(lambda x: F'<p data-genes="{x[1]}">{x[0]}</p>')

        return self.pandas_to_html(table, id=F'table_{grp_id}')

    def __get_count_gene_tuple(self, genome: Genome, anno: Annotation) -> (int, list):
        genes = list(anno.gene_set.filter(genomecontent__genome=genome).values_list('identifier', flat=True))
        genes_to_js = ' '.join(genes)
        return len(genes), genes_to_js

    def __count_genes(self, genome: Genome, anno: Annotation) -> int:
        return anno.gene_set.filter(genomecontent__genome=genome).count()

    def __create_coverage_matrix(self) -> (pd.DataFrame, dict):
        pattern_to_genomes = self.create_patterns()

        tmp_grp_to_genomes = dict()
        tmp_grp_to_pattern = dict()
        for i, (pattern, genomes) in enumerate(pattern_to_genomes.items()):
            tmp_grp_to_genomes[F'tmp_grp{i}'] = genomes
            tmp_grp_to_pattern[F'tmp_grp{i}'] = pattern

        matrix = pd.DataFrame(tmp_grp_to_pattern)
        matrix.index = self.annotations

        # sort by most prevalent annotations and most common group
        matrix = matrix.reindex(matrix.sum(axis=0).sort_values(ascending=False).index, axis=1)
        matrix = matrix.reindex(matrix.sum(axis=1).sort_values(ascending=False).index, axis=0)

        # create groups: e.g. [[genome2, genome8], [genome1], ... ]
        grp_to_genomes = {F'g{i}': tmp_grp_to_genomes[tmp_grp] for i, tmp_grp in enumerate(matrix.columns)}

        # create final group names
        matrix.columns = grp_to_genomes.keys()

        return matrix, grp_to_genomes

    def create_patterns(self) -> dict:
        pattern_to_genomes = {}
        for genome in self.genomes:
            pattern = self.get_pattern(genome)
            if pattern in pattern_to_genomes:
                pattern_to_genomes[pattern].append(genome)
            else:
                pattern_to_genomes[pattern] = [genome]
        return pattern_to_genomes

    def get_pattern(self, genome: Genome) -> tuple:
        """
        :returns a tuple of len(annotations) filled with booleans: True if genome covers annotation
        Example: (False, False, False, True, False)
        """
        pattern = list()
        for annotation in self.annotations:
            try:
                annotation.genomecontent_set.get(identifier=genome.identifier)
                pattern.append(True)
            except GenomeContent.DoesNotExist:
                pattern.append(False)
        return tuple(pattern)  # tuples are hashable
