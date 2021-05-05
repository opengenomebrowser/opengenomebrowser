import os
from django.db import models
from website.models import TaxID, GenomeSimilarity, Annotation, Genome, GenomeContent, Organism, CoreGenomeDendrogram
import pandas as pd
from biotite.sequence.phylo import upgma


class TreeNotDoneError(Exception):
    def __init__(self, message):
        self.message = message


class TreeFailedError(Exception):
    def __init__(self, message):
        self.message = message


class AbstractTree:
    @property
    def newick(self):
        raise NotImplementedError('AbstractTree cannot create trees')


class TaxIdTree(AbstractTree):
    """
    Create a Newick tree based on taxonomy.

    :param objs: QuerySet of class 'GenomeContent', 'Genome', 'Organism' or 'TaxID'
                    -> require property 'parent' that points to TaxID
    """

    def __init__(self, objs):
        # transform QuerySet into TaxID-Queryset
        assert type(objs) == models.QuerySet

        # Load necessary TaxIDs into dictionary
        node_to_children = {}  # TaxID (parent) -> set(TaxID, TaxID) (children)
        for taxid in objs:
            # assert taxid.invariant()  # ensure it has parents up until root node
            while taxid.parent:
                if taxid.parent in node_to_children:
                    node_to_children[taxid.parent].add(taxid)
                else:
                    node_to_children[taxid.parent] = {taxid}
                taxid = taxid.parent

        root_node = TaxID.objects.get(parent=None)
        assert root_node in node_to_children

        # Create Newick-string using recursion.
        def newick_render_node(taxid: TaxID) -> str:
            # recursive function: start with root node, let children render themselves
            if taxid not in node_to_children:
                return str(taxid)
            else:
                children_set = node_to_children[taxid]
                children_strings = [newick_render_node(child) for child in children_set]
                return "(" + ','.join(children_strings) + ")" + str(taxid)

        self.__newick = newick_render_node(root_node)

    @property
    def newick(self) -> str:
        return self.__newick


class AniTree(AbstractTree):
    """
    Create a Newick tree based on ANI whole genome similarity.

    :param genomes: QuerySet of class 'Genome'
    :raises TreeNotDoneError: if ANI-calculation is still running. (Be sure huey is running! (./manage.py run_huey))
    """

    def __init__(self, genomes: models.QuerySet):
        anis = []
        for g1 in genomes:
            for g2 in genomes:
                if g1 == g2:
                    ani, created = GenomeSimilarity.objects.get_or_create(from_genome=g1, to_genome=g2)
                    anis.append(ani)
                    break

                assert os.path.isfile(g1.genome.assembly_fasta(relative=False)), g1.genome.assembly_fasta(rel_path=False)
                assert os.path.isfile(g2.genome.assembly_fasta(relative=False)), g2.genome.assembly_fasta(rel_path=False)
                ani, created = GenomeSimilarity.objects.get_or_create(from_genome=g1, to_genome=g2)
                anis.append(ani)

        self.__anis = anis
        self.__genomes = genomes

    @property
    def newick(self) -> str:
        def get_status(ani: GenomeSimilarity):
            ani.refresh_from_db()
            return ani.status

        states = [get_status(ani) for ani in self.__anis]

        n_done = states.count('D')
        n_running = states.count('R')
        n_failed = states.count('F')

        assert n_done + n_running + n_failed == len(self.__anis)

        if n_failed > 0:
            TreeFailedError('Similarity calculations failed. ' +
                             F'Finished: {n_done}, running: {n_running}, failed: {n_failed}')

        if n_running > 0:
            raise TreeNotDoneError('Similarities are still being calculated. ' +
                                   F'Finished: {n_done}, running: {n_running}')

        similarity_matrix = pd.DataFrame(
            {g1.identifier: [GenomeSimilarity.objects.get(g1, g2).similarity for g2 in self.__genomes]
             for g1 in self.__genomes})
        similarity_matrix.rename({n: id for n, id in enumerate(self.__genomes.values_list('identifier', flat=True))},
                                 inplace=True)

        self.distance_matrix = 1 - similarity_matrix

        self._tree = upgma(self.distance_matrix.values)
        return self._tree.to_newick(labels=self.distance_matrix.index)


class OrthofinderTree(AbstractTree):
    """
    Create a Newick tree using Orthofinder. (https://github.com/davidemms/OrthoFinder)

    :param genomes: QuerySet of class 'Genome'
    :raises TreeNotDoneError: if Orthofinder failed or is still running. (Be sure huey is running! (./manage.py run_huey))
    """

    def __init__(self, genomes: models.QuerySet):
        self.__genomes = genomes
        self.__dendrogram, created = CoreGenomeDendrogram.objects.get_or_create(genomes=genomes)

    @property
    def newick(self) -> str:
        self.__dendrogram.refresh_from_db()

        status = self.__dendrogram.status

        if status == 'D':
            return self.__dendrogram.newick
        if status == 'R':
            raise TreeNotDoneError('Tree is still being calculated...')
        if status == 'F':
            raise TreeFailedError(f'Tree calculation failed. {self.__dendrogram.message}')

        raise AssertionError('Code should never end up here!')
