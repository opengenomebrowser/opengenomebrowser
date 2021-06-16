import numpy as np
import pandas as pd
from collections import Counter
from itertools import combinations

from django.db import connection, models
from website.models import TaxID, GenomeSimilarity, CoreGenomeDendrogram, GenomeContent

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


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class AniTree(AbstractTree):
    """
    Create a Newick tree based on ANI whole genome similarity.

    :param genomes: QuerySet of class 'Genome'
    :raises TreeNotDoneError: if ANI-calculation is still running. (Be sure huey is running! (./manage.py run_huey))
    """

    def __init__(self, genomes: models.QuerySet):
        self.identifiers = sorted(genomes.values_list("identifier", flat=True))

    @staticmethod
    def __fetch_similarities(identifier_combinations: tuple[str, str]) -> [(str, str, float, str)]:
        with connection.cursor() as cursor:
            values = []
            for chunk in chunks(identifier_combinations, 5000):
                cursor.execute(f'''
                    SELECT from_genome_id, to_genome_id, similarity, status
                    FROM public.website_genomesimilarity 
                    WHERE (from_genome_id, to_genome_id) IN %s''', [chunk])
                values.extend(cursor.fetchall())
        return values

    @classmethod
    def create_distance_matrix(cls, identifiers: [str], values: [(str, str, float, str)]) -> pd.DataFrame:
        # create pivot table
        result = pd.DataFrame(
            data=[(i, i) for i in identifiers] + values,  # prepend makes index and columns of pivoted table identical to self.identifiers
            columns=['from_genome_id', 'to_genome_id', 'similarity', 'status']
        ).pivot(
            index='from_genome_id', columns='to_genome_id', values='similarity'
        )  # resulting DataFrame has result in upper triangle only

        assert (identifiers == result.index).all() and (identifiers == result.columns).all(), \
            f'resultFrame pivot index/columns should match identifiers.\n{result.index=}\n{result.columns=}\n{identifiers=}'

        # this resultFrame is a triangular matrix, turn it into a symmetrical matrix
        result = np.triu(result, 1)  # upper triangle of an array, excluding the diagonal
        result = result + result.T  # make symmetrical array
        np.fill_diagonal(result, 1)  # fill diagonal with 1

        result = pd.DataFrame(result, index=identifiers, columns=identifiers)
        assert not result.isna().values.any(), f'This matrix should not contain any nan-values!'

        return 1 - result  # turn similarity matrix into distance matrix

    @classmethod
    def calculate_similarities(cls, identifiers: [str]) -> (bool, int, int, int, [(str, str, float, str)]):
        # itertools.combinations only contain unique combinations and no combinations of the same element
        # because the identifiers are sorted, it is ensured that in the combinations, the 'smaller' genome is always first
        identifier_combinations = tuple(combinations(identifiers, 2))

        values = cls.__fetch_similarities(identifier_combinations=identifier_combinations)

        n_missing = len(identifier_combinations) - len(values)

        if n_missing:
            should_have = set(identifier_combinations)
            have = set((from_genome, to_genome) for from_genome, to_genome, similarity, status in values)
            missing = should_have.difference(have)
            for from_genome, to_genome in missing:
                gs, created = GenomeSimilarity.objects.get_or_create(
                    from_genome=GenomeContent.objects.get(identifier=from_genome),
                    to_genome=GenomeContent.objects.get(identifier=to_genome)
                )

        counter = Counter(status for from_genome, to_genome, similarity, status in values)

        n_done = counter.get('D', 0)
        n_running = counter.get('R', 0) + n_missing
        n_failed = counter.get('F', 0)
        complete = n_done == len(identifier_combinations)

        assert n_done + n_running + n_failed == len(identifier_combinations), \
            f'{n_done=} + {n_running=} + {n_failed=} == {len(identifier_combinations)=}'

        return complete, n_done, n_running, n_failed, values

    @property
    def newick(self) -> str:
        complete, n_done, n_running, n_failed, values = self.calculate_similarities(identifiers=self.identifiers)

        if not complete:
            # raise error
            msg = f'{complete=}, {n_done=}, {n_running=}, {n_failed=}'
            if n_failed > 0:
                raise TreeFailedError('Similarity calculations failed. ' + msg)
            elif n_running > 0:
                raise TreeNotDoneError('Similarities are still being calculated. ' + msg)
            else:
                raise TreeFailedError('A strange error occurred. Please contact the developer. ' + msg)

        self.distance_matrix = self.create_distance_matrix(identifiers=self.identifiers, values=values)
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

    @property
    def has_cache_file(self):
        return self.__dendrogram.has_cache_file

    @property
    def cache_file_path(self):
        return self.__dendrogram.cache_file_path(relative=True)
