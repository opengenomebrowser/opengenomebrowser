from django.shortcuts import render, HttpResponse
from django.db.models import Q, Count, Exists
from django.contrib.postgres.aggregates.general import ArrayAgg

import pandas as pd
import json

from website.models import Genome, Gene, GenomeContent
from website.models.Annotation import Annotation
from website.views.helpers.extract_requests import contains_data, extract_data

from .GenomeDetailView import dataframe_to_bootstrap_html

from .helpers.magic_string import MagicQueryManager


# todo: make the queries more efficient. do not add genes to cell, do that with javascript later?
#  maybe don't load gene count after n*n = 200 cells?
#  maybe annotate Annotation queryset as opposed to Genome queryset?

def annotation_view(request):
    context = dict(
        title='Annotation search',
        error_danger=[], error_warning=[], error_info=[]
    )

    if contains_data(request, 'genomes'):
        qs = extract_data(request, 'genomes', list=True)

        try:
            magic_query_manager = MagicQueryManager(queries=qs)
            context['magic_query_manager'] = magic_query_manager
            context['genome_to_species'] = magic_query_manager.genome_to_species()
            if len(magic_query_manager.all_genomes) == 0:
                context['error_danger'].append('Query did not find any genomes.')
        except Exception as e:
            context['error_danger'].append(str(e))

    if contains_data(request, 'annotations'):
        annotation_name_list = extract_data(request, 'annotations', list=True)
        annotations = Annotation.objects.filter(name__in=annotation_name_list)
        context['annotations'] = annotations
        found_annotations = set(annotations.values_list('name', flat=True))
        if not len(annotation_name_list) == len(found_annotations):
            context['error_danger'].append(
                F'Could not interpret these annotations: {set(annotation_name_list).symmetric_difference(found_annotations)}')

    return render(request, 'website/annotation_search.html', context)


def matrix(request):
    # check input
    if not 'genomes[]' and 'annotations[]' in request.POST:
        return HttpResponse('Request failed! Please POST genomes[] and annotations[].')

    qs = set(request.POST.getlist('genomes[]'))

    try:
        magic_query_manager = MagicQueryManager(qs)
    except Exception as e:
        return HttpResponse(F'Request failed: genomes[] incorrect. {e}')

    annotations = set(request.POST.getlist('annotations[]'))
    if len(annotations) == 0:
        return HttpResponse('Request failed: annotations[] empty.')
    try:
        annotations = [Annotation.objects.get(name=anno.replace('!!!', ' ')) for anno in annotations]
    except Annotation.DoesNotExist:
        return HttpResponse('Request failed: annotations[] incorrect.')

    all_genomes = magic_query_manager.all_genomes

    mm = MatrixMaker(all_genomes, annotations)

    context = dict(
        matrix_header=mm.coverage_matrix.columns.to_list(),
        matrix_body=zip(mm.coverage_matrix.index, mm.coverage_matrix.values.tolist()),
        matrix_footer_covered=mm.coverage_matrix.sum().values.tolist(),
        matrix=mm.html_matrix
    )

    return render(request, 'website/annotation_search_matrix.html', context)


class MatrixMaker:
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

    def __pattern_to_rank(self, matrix, axis: int):
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
