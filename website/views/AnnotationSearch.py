from django.shortcuts import render, HttpResponse
import pandas as pd

from website.models import Genome, Gene
from website.models.Annotation import Annotation


def annotation_view(request):
    context = {}

    if 'members' in request.GET:
        context['key_members'] = request.GET['members'].split(' ')

    if 'annotations' in request.GET:
        context['key_annotations'] = [ann.replace('!!!', ' ') for ann in request.GET['annotations'].split(' ')]

    return render(request, 'website/annotation_search.html', context)


def annotation_matrix(request):
    context = {}

    # check input
    if not 'members[]' and 'annotations[]' in request.POST:
        return HttpResponse('Request failed! Please POST members[] and annotations[].')

    identifiers = set(request.POST.getlist('members[]'))
    genomes = Genome.objects.filter(identifier__in=identifiers).order_by('identifier')

    if len(identifiers) != len(genomes):
        return HttpResponse('Request failed: members[] incorrect.')

    annotations = set(request.POST.getlist('annotations[]'))
    try:
        annotations = [Annotation.objects.get(name=anno.replace('!!!', ' ')) for anno in annotations]
    except Annotation.DoesNotExist:
        return HttpResponse('Request failed: annotations[] incorrect.')

    mm = MatrixMaker(genomes, annotations)
    grp_to_genomes_annogene = mm.get_grp_to_genomes_annogene()

    print(grp_to_genomes_annogene)

    context = dict(
        table_header=mm.matrix.columns.to_list(),
        table_body=zip(mm.matrix.index, mm.matrix.values.tolist()),
        table_footer_covered=mm.matrix.sum().values.tolist(),
        table_footer_members=[len(g) for g in mm.grp_to_genomes.values()],
        grp_to_genomes_annogene=grp_to_genomes_annogene
    )

    return render(request, 'website/annotation_matrix.html', context)


class MatrixMaker:
    def __init__(self, genomes: [Genome], annotations: [Annotation]):
        self.genomes = genomes
        self.annotations = annotations

        self.matrix, \
        self.grp_to_genomes = self.__create_coverage_matrix()

        self.grp_to_genes = self.__get_grp_to_genes()

    def get_grp_to_genomes_annogene(self):
        return {grp: (genomes, self.grp_to_genes[grp]) for grp, genomes in self.grp_to_genomes.items()}

    def __get_grp_to_genes(self):
        grp_to_genes = dict()
        for group_name, genomes in self.grp_to_genomes.items():
            print(group_name, len(genomes))
            grp_to_genes[group_name] = []
            for annotation, is_covered in self.matrix[group_name].items():
                if is_covered:
                    genes = self.get_genes(annotation, genomes)
                    assert len(genomes) <= len(genes), F'There must be at least as many genes as genomes! {annotation}\n{genomes}\n{genes}'
                    grp_to_genes[group_name].append((annotation, genes))

        return grp_to_genes

    @staticmethod
    def get_genes(annotation: Annotation, genomes: [Genome]) -> [Gene]:
        return annotation.gene_set.filter(genome__in=genomes).order_by('genome__identifier').prefetch_related('genome__member__strain__taxid')

    def __create_coverage_matrix(self):
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
                annotation.genome_set.get(identifier=genome.identifier)
                pattern.append(True)
            except Genome.DoesNotExist:
                pattern.append(False)
        return tuple(pattern)  # tuples are hashable
