from website.models import Genome, TaxID
from django.http import JsonResponse
from django.db.models import ObjectDoesNotExist, QuerySet, Model


class MagicError(Exception):
    def __init__(self, message):
        self.message = message


class MagicObject:
    """
    Python object for "Magic Strings"

    Terms:
        magic string: @taxclass:Bacilli
            refers to all Genomes that belong to the taxonomic class of Bacilli
            consists of @{magic_word}:{query}

        magic_word:
            e.g. taxclass
            refers to a category to be filtered
    """

    MAGIC_WORDS = [
        'tax',  # shorthand for taxscientificname
        'taxsuperkingdom',
        'taxphylum',
        'taxclass',
        'taxorder',
        'taxfamily',
        'taxgenus',
        'taxspecies',
        'taxsubspecies'
    ]

    def __init__(self, magic_string: str):
        assert magic_string.startswith('@')

        self.safe_string = magic_string.replace(' ', '!!!')
        self.magic_string = magic_string.replace('!!!', ' ')

        magic_word, query = self.magic_string[1:].split(':', maxsplit=1)

        if query is None:
            query = ''

        if magic_word not in self.MAGIC_WORDS:
            raise MagicError(F'Magic word is invalid: {magic_word} - {query}.')

        try:
            if magic_word == 'tax':
                self.obj = TaxID.objects.get(taxscientificname=query)
            elif magic_word.startswith('tax'):
                self.obj = TaxID.objects.get(taxscientificname=query, **{'rank': magic_word[3:]})
            else:
                raise MagicError(F'Failed to process magic word! {magic_word}')

        except ObjectDoesNotExist as e:
            raise MagicError(F'Could not find magic_string object: {magic_string}.')

    def __str__(self):
        return self.magic_string

    @property
    def html(self):
        return F'<div class="genome ogb-tag" data-species="{self.scientific_name}" data-toggle="tooltip" title="">{self.magic_string}</div>'

    @property
    def scientific_name(self):
        return self.obj.taxscientificname

    @property
    def taxid(self):
        return self.obj.id

    def genomes(self, representative=True, contaminated=False, restricted=False):
        return self.obj.get_child_genomes(representative=representative, contaminated=contaminated, restricted=restricted)

    @staticmethod
    def autocomplete(magic_string: str) -> [dict]:
        results = []
        if ':' not in magic_string:
            # show magic words themselves
            words_left = [w for w in MagicObject.MAGIC_WORDS if magic_string[1:] in w]
            for w in words_left:
                results.append({
                    'label': F"@{w} (magic word)",
                    'value': F"@{w}:"
                })

        else:
            magic_word, query = magic_string[1:].split(':', maxsplit=1)

            if magic_word not in MagicObject.MAGIC_WORDS:
                raise MagicError(F'Magic word does not exist: {magic_word}.')

            # process taxids
            if magic_word.startswith('tax'):
                if magic_word == 'tax':
                    attr = 'taxscientificname'
                    taxids = TaxID.objects.filter(taxscientificname__icontains=query)
                else:
                    attr = magic_word
                    taxids = TaxID.objects.filter(taxscientificname__icontains=query, **{'rank': magic_word[3:]})

                taxids = taxids[:20]
                for taxid in taxids:
                    results.append({
                        'label': F"@{magic_word}:{getattr(taxid, attr)}",
                        'value': F"@{magic_word}:{getattr(taxid, attr)}"
                    })
            else:
                raise MagicError(F'Failed to process magic word! {magic_word}')

        return results


class MagicQueryManager:
    """
    Helper class to validate, autocomplete and manage queries that consist of genome identifiers and "magic strings"

    Terms:
        queries:
            genome identifiers or magic strings
            e.g.: ['genome-1', 'genome-2', '@taxclass:Bacilli']

        magic_string:
            e.g. @taxclass:Bacilli
            refers to all Genomes that belong to the taxonomic class of Bacilli
            consists of @{magic_word}:{query}

        magic_word:
            e.g. taxclass
            refers to a category to be filtered
    """

    def __init__(self, queries: [str]):
        self.queries = queries
        self.genome_identifiers, \
        self.magic_strings = self.__split_queries(queries)

        self.regular_genomes = self.__load_regular_genomes()
        self.magic_objects = self.__load_magic_objects()

        self._magic_genomes = None
        self._all_genomes = None

    @property
    def magic_genomes(self):
        if self._magic_genomes is None:
            self._magic_genomes = self.__load_magic_genomes()
        return self._magic_genomes

    @property
    def all_genomes(self):
        if self._all_genomes is None:
            all_genomes = self.regular_genomes.all()  # deep copy
            self._all_genomes = all_genomes.union(self.magic_genomes)
        return self._all_genomes

    def genome_to_species(self, regular_genomes=True, magic_genomes=True, magic_objects=True):
        genome_to_species = dict()
        if regular_genomes:
            genome_to_species.update(self.__genomes_to_species(self.regular_genomes))
        if magic_genomes:
            genome_to_species.update(self.__genomes_to_species(self.magic_genomes))
        if magic_objects:
            genome_to_species.update(self.__magic_object_to_species(self.magic_objects))

        return genome_to_species

    @staticmethod
    def __magic_object_to_species(magic_objects: [MagicObject]):
        return {
            magic_object.magic_string: dict(
                taxid=magic_object.taxid,
                sciname=magic_object.scientific_name
            ) for magic_object in magic_objects
        }

    @staticmethod
    def __genomes_to_species(genomes: QuerySet):
        return {
            genome['identifier']: dict(
                taxid=genome['organism__taxid'],
                sciname=genome['organism__taxid__taxscientificname']
            )
            for genome in genomes.values('identifier', 'organism__taxid', 'organism__taxid__taxscientificname')
        }

    @classmethod
    def __split_queries(cls, queries: [str]) -> ({str}, {str}):
        """split queries into regular genome identifiers and magic strings"""
        genome_identifiers, magic_strings = set(), set()
        for q in queries:
            if q.startswith('@'):
                magic_strings.add(q)
            else:
                genome_identifiers.add(q.replace('!!!', ' '))
        return genome_identifiers, magic_strings

    def __load_magic_objects(self) -> [MagicObject]:
        return [MagicObject(magic_string) for magic_string in self.magic_strings]

    def __load_regular_genomes(self):
        # process regular identifiers
        genomes = Genome.objects.filter(identifier__in=self.genome_identifiers).prefetch_related('organism', 'organism__taxid')
        if len(genomes) != len(self.genome_identifiers):
            raise MagicError(F"Could not find all genomes!'")
        return genomes

    def __load_magic_genomes(self):
        genomes = Genome.objects.none()
        for magic_object in self.magic_objects:
            genomes = genomes.union(magic_object.genomes())
        return genomes
