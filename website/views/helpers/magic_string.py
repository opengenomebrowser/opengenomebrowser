from website.models import Genome, TaxID
from django.http import JsonResponse
from django.db.models import ObjectDoesNotExist, QuerySet, Model


class MagicString:
    """
    Helper class to validate, autocomplete and manage "Magic Strings"

    Terms:
        magic_string:
            e.g. @taxclass:Bacilli
            refers to all Genomes that belong to the taxonomic class of Bacilli
            consists of @{magic_word}:{query}

        magic_word:
            e.g. taxclass
            refers to a category to be filtered

        query:
            e.g. Bacilli
            what the category should be filtered by

        queries:
            not to be confused by queries
            genome identifiers or magic strings
            e.g.: ['genome-1', 'genome-2', '@taxclass:Bacilli']

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

    @classmethod
    def __split_query(cls, queries: [str]) -> ({str}, {str}):
        """split queries into regular genome identifiers and magic strings"""
        genome_identifiers, magic_words = set(), set()
        for q in queries:
            if q.startswith('@'):
                magic_words.add(q)
            else:
                genome_identifiers.add(q.replace('!!!', ' '))
        return genome_identifiers, magic_words

    @classmethod
    def validate(cls, queries: [str]):
        """
        :raises ValueError
        """
        genome_identifiers, magic_strings = cls.__split_query(queries)

        # validate genome_identifiers
        found_genomes = set(Genome.objects.filter(identifier__in=genome_identifiers).values_list('identifier', flat=True))
        if not genome_identifiers == found_genomes:
            raise ValueError('Could not find some identifiers.')

        # validate magic_strings
        for magic_string in magic_strings:
            if not cls.magic_string_isvalid(magic_string):
                raise ValueError(F'TaxID does not exist: {magic_string}.')

    @classmethod
    def autocomplete(cls, magic_string: str) -> []:
        results = []
        if ':' not in magic_string:
            # show magic words themselves
            words_left = [w for w in MagicString.MAGIC_WORDS if magic_string[1:] in w]
            for w in words_left:
                results.append({
                    'label': F"@{w} (magic word)",
                    'value': F"@{w}:"
                })

        else:
            magic_word, query = magic_string[1:].split(':', maxsplit=1)

            if magic_word not in MagicString.MAGIC_WORDS:
                raise ValueError(F'Magic word does not exist: {magic_word}.')

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
                raise AssertionError(F'Failed to process magic word! {magic_word}')

        return results

    @classmethod
    def to_species(cls, queries: [str]) -> {}:
        genome_to_species = dict()

        genome_identifiers, magic_strings = cls.__split_query(queries)

        # process genome_identifiers
        genome_queryset = Genome.objects.filter(identifier__in=genome_identifiers).prefetch_related('strain', 'strain__taxid') \
            .values('identifier', 'strain__taxid', 'strain__taxid__taxscientificname')

        for m in genome_queryset:
            genome_to_species[m['identifier']] = dict(
                taxid=m['strain__taxid'],
                sciname=m['strain__taxid__taxscientificname']
            )

        if len(genome_to_species) != len(genome_identifiers):
            missing = set(genome_identifiers).difference(set(genome_to_species.keys()))
            raise ValueError(F"could not find genome for genomes='{missing}'")

        # process magic_words
        for magic_string in magic_strings:
            magic_object = cls.get_magic_object(magic_string)

            genome_to_species[magic_string] = dict(
                taxid=cls.__get_taxid(magic_object),
                sciname=cls.__get_taxscientificname(magic_object)
            )

        return genome_to_species

    @classmethod
    def get_magic_object(cls, magic_string: str) -> Model:
        """
        :returns object

        :raises ValueError upon error
        """
        magic_string = magic_string.replace('!!!', ' ')

        magic_word, query = magic_string[1:].split(':', maxsplit=1)

        if magic_word not in cls.MAGIC_WORDS:
            raise ValueError(F'Magic word does not exist: {magic_word} - {query}.')

        try:

            if magic_word == 'tax':
                obj = TaxID.objects.get(taxscientificname=query)
            elif magic_word.startswith('tax'):
                obj = TaxID.objects.get(taxscientificname=query, **{'rank': magic_word[3:]})
            else:
                raise AssertionError(F'Failed to process magic word! {magic_word}')

        except ObjectDoesNotExist as e:
            raise ValueError(F'Could not find magic_string object: {magic_string}.')

        return obj

    @classmethod
    def magic_string_isvalid(cls, magic_string: str) -> bool:
        magic_string = magic_string.replace('!!!', ' ')

        try:
            magic_object = cls.get_magic_object(magic_string=magic_string)
        except ValueError as e:
            return False
        return True

    @classmethod
    def get_genomes(cls, queries: [str]) -> QuerySet:
        genome_identifiers, magic_strings = cls.__split_query(queries)

        # process regular identifiers
        genomes = Genome.objects.filter(identifier__in=genome_identifiers)
        if len(genomes) != len(genome_identifiers):
            raise ValueError(F"Could not find all genomes!'")

        # process magic strings
        for magic_string in magic_strings:
            magic_object = cls.get_magic_object(magic_string)
            genomes = genomes.union(cls.__get_genomes(magic_object))

        genomes = genomes.order_by('identifier')

        return genomes

    @classmethod
    def __get_genomes(cls, magic_object) -> QuerySet:
        if type(magic_object) is TaxID:
            magic_object: TaxID
            return magic_object.get_child_genomes(representative=True, contaminated=False, restricted=False)

    @classmethod
    def __get_taxid(cls, magic_object) -> str:
        if type(magic_object) is TaxID:
            return magic_object.id

    @classmethod
    def __get_taxscientificname(cls, magic_object) -> str:
        if type(magic_object) is TaxID:
            return magic_object.taxscientificname
