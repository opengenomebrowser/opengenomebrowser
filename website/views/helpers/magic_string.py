from website.models import Genome, TaxID, Tag
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
        'taxsubspecies',

        'tag'
    ]

    def __init__(self, magic_string: str):
        assert magic_string.startswith('@')

        self.magic_string = magic_string

        magic_word, query = self.magic_string[1:].split(':', maxsplit=1)

        if query is None:
            query = ''

        if magic_word not in self.MAGIC_WORDS:
            raise MagicError(f'Magic word is invalid: {magic_word} - {query}.')

        try:
            if magic_word == 'tax':
                self.obj = TaxID.objects.get(taxscientificname=query)
            elif magic_word.startswith('tax'):
                self.obj = TaxID.objects.get(taxscientificname=query, **{'rank': magic_word[3:]})
            elif magic_word == 'tag':
                self.obj = Tag.objects.get(tag=query)
            else:
                raise MagicError(f'Failed to process magic word! {magic_word}')

        except ObjectDoesNotExist:
            raise MagicError(f'Could not find magic_string object: {magic_string}.')

    def __str__(self):
        return self.magic_string

    @property
    def html(self):
        if type(self.obj) is TaxID:
            return f'<div class="genome ogb-tag" data-species="{self.obj.taxscientificname}" title="">{self.magic_string}</div>'
        elif type(self.obj) is Tag:
            return self.obj.html
        else:
            raise MagicError(f'MagicWord obj is of unknown type: {type(self.obj)}')

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
                raise MagicError(f'Magic word does not exist: {magic_word}.')

            if magic_word.startswith('tax'):
                # process taxids
                if magic_word == 'tax':
                    attr = 'taxscientificname'
                    taxids = TaxID.objects.filter(taxscientificname__icontains=query)[:20]
                else:
                    attr = magic_word
                    taxids = TaxID.objects.filter(taxscientificname__icontains=query, **{'rank': magic_word[3:]})[:20]

                for taxid in taxids:
                    results.append({
                        'label': F"@{magic_word}:{getattr(taxid, attr)}",
                        'value': F"@{magic_word}:{getattr(taxid, attr)}"
                    })
            elif magic_word == 'tag':
                # process tags
                tags = Tag.objects.filter(tag__icontains=query)[:20]

                for tag in tags:
                    results.append({
                        'label': F"@{magic_word}:{tag.tag}",
                        'value': F"@{magic_word}:{tag.tag}"
                    })

            else:
                raise MagicError(f'Failed to process magic word! {magic_word}')

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

    def __init__(self, queries: [str], raise_errors=True):
        self.queries = set(queries)
        self.raise_errors = raise_errors

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

    def __magic_object_to_species(self, magic_objects: [MagicObject]):
        result = {}
        for magic_object in magic_objects:
            if type(magic_object.obj) is TaxID:
                result[magic_object.magic_string] = dict(
                    type='taxid',
                    taxid=magic_object.obj.id,
                    sciname=magic_object.obj.taxscientificname
                )
            elif type(magic_object.obj) is Tag:
                result[magic_object.magic_string] = dict(
                    type='tag',
                    tag=magic_object.obj.tag,
                    description=magic_object.obj.description
                )
            else:
                if self.raise_errors:
                    raise MagicError(f'Magic Object obj is of unknown type: {type(magic_object.obj)}')
        return result

    @staticmethod
    def __genomes_to_species(genomes: QuerySet):
        return {
            genome['identifier']: dict(
                type='genome',
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
                genome_identifiers.add(q)
        return genome_identifiers, magic_strings

    def __load_magic_objects(self) -> [MagicObject]:
        return [MagicObject(magic_string) for magic_string in self.magic_strings]

    def __load_regular_genomes(self):
        # process regular identifiers
        genomes = Genome.objects.filter(identifier__in=self.genome_identifiers).prefetch_related('organism', 'organism__taxid')
        if self.raise_errors and len(genomes) != len(self.genome_identifiers):
            raise MagicError(F"Could not find all genomes!")
        return genomes

    def __load_magic_genomes(self):
        genomes = Genome.objects.none()
        for magic_object in self.magic_objects:
            genomes = genomes.union(magic_object.genomes())
        return genomes
