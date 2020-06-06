from django.shortcuts import render, HttpResponse
import pandas as pd

from website.models import GenomeContent, Gene
from website.models.Annotation import Annotation


def annotation_view(request):
    context = dict(title='Annotation search')

    if 'genomes' in request.GET:
        context['key_genomes'] = request.GET['genomes'].split(' ')

    if 'annotations' in request.GET:
        annotation_name_list = [ann.replace('!!!', ' ') for ann in request.GET['annotations'].split(' ')]
        context['key_annotations'] = Annotation.objects.filter(name__in=annotation_name_list).values_list('name', flat=True)

    return render(request, 'website/annotation_search.html', context)


def annotation_matrix(request):
    context = {}

    # check input
    if not 'genomes[]' and 'annotations[]' in request.POST:
        return HttpResponse('Request failed! Please POST genomes[] and annotations[].')

    identifiers = set(request.POST.getlist('genomes[]'))
    genomes = GenomeContent.objects.filter(identifier__in=identifiers).order_by('identifier')

    if len(identifiers) != len(genomes):
        return HttpResponse('Request failed: genomes[] incorrect.')

    annotations = set(request.POST.getlist('annotations[]'))
    try:
        annotations = [Annotation.objects.get(name=anno.replace('!!!', ' ')) for anno in annotations]
    except Annotation.DoesNotExist:
        return HttpResponse('Request failed: annotations[] incorrect.')

    mm = MatrixMaker(genomes, annotations)

    group_to_table = mm.get_group_to_table()

    context = dict(
        matrix_header=mm.matrix.columns.to_list(),
        matrix_body=zip(mm.matrix.index, mm.matrix.values.tolist()),
        matrix_footer_covered=mm.matrix.sum().values.tolist(),
        matrix_footer_genomes=[len(g) for g in mm.grp_to_genomes.values()],
        matrix=mm.html_matrix,
        group_to_table=group_to_table
    )

    return render(request, 'website/annotation_matrix.html', context)


class MatrixMaker:
    def __init__(self, genomes: [GenomeContent], annotations: [Annotation]):
        self.genomes = genomes

        self._genome_to_html = {}  # cannot be done using list comprehension
        for genome in genomes:
            self._genome_to_html[genome] = genome.genome.html

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
        html = tmp.to_html(escape=False)

        html = html \
            .replace('border="1" class="dataframe"',
                     F'id="{id}" class="table table-bordered table-sm white-links"', 1) \
            .replace('<thead>', '<thead class="thead-dark">', 1) \
            .replace('<th>g', '<th scope="col">g', len(table.columns))

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
    def get_genes(annotation: Annotation, genomes: [GenomeContent]) -> [Gene]:
        return annotation.gene_set.filter(genomecontent__in=genomes).order_by('genomecontent__identifier').prefetch_related('genomecontent__genome__strain__taxid')

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

    def __get_count_gene_tuple(self, genome: GenomeContent, anno: Annotation) -> (int, list):
        genes = list(anno.gene_set.filter(genomecontent=genome).values_list('identifier', flat=True))
        genes_to_js = ' '.join(genes)
        return len(genes), genes_to_js

    def __count_genes(self, genome: GenomeContent, anno: Annotation) -> int:
        return anno.gene_set.filter(genomecontent=genome).count()

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

    def get_pattern(self, genome: GenomeContent) -> tuple:
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
