import os
import re
from django.db import models
from django.utils.translation import gettext_lazy as _
from binary_file_search.BinaryFileSearch import BinaryFileSearch
from lib.gene_ontology.gene_ontology import GeneOntology
from enum import Enum
from OpenGenomeBrowser import settings

gene_ontology = GeneOntology()

FILENAME_SETTINGS = {
    'ko.tsv': ('ko:', 'lib/custom_kegg/data/rest_data/ko.tsv'),
    'rn.tsv': ('rn:', 'lib/custom_kegg/data/rest_data/rn.tsv'),
    'compound.tsv': ('cpd:', 'lib/custom_kegg/data/rest_data/rn.tsv'),
    'orthologs.tsv': settings.ORTHOLOG_ANNOTATIONS['ortholog_to_name'] if 'ortholog_to_name' in settings.ORTHOLOG_ANNOTATIONS else '/dev/null'
}


class AnnotationRegex(Enum):
    def __init__(self, value, match_regex, start_regex):
        self._value_ = value
        self.match_regex = match_regex
        self.start_regex = start_regex

    CUSTOM = ('CU', re.compile('^C\:[0-9a-zA-Z\-\_\:\.]{1,48}$'), re.compile('^C\:[0-9a-zA-Z\-\_\:\.]{1,48}$'))
    ENZYMECOMMISSION = ('EC', re.compile('^EC:[0-9\.-]{1,12}$'), re.compile('^[Ee][Cc]:[0-9\.-]{1,12}$'))
    KEGGGENE = ('KG', re.compile('^K[0-9]{5}$'), re.compile('^[Kk][0-9]{1,5}$'))
    KEGGREACTION = ('KR', re.compile('^R[0-9]{5}$'), re.compile('^[Rr][0-9]{1,5}$'))
    GENEONTOLOGY = ('GO', re.compile('^GO:[0-9]{7}$'), re.compile('^[Gg][Oo]:[0-9]{1,7}$'))
    ORTHOLOG = ('OL', re.compile('^HOG[0-9]{7}$'), re.compile('^[Oo][Gg][0-9]{1,7}$'))
    GENECODE = ('GC', re.compile('^[0-9a-zA-Z\_\/\-\ \']{3,11}$'), re.compile('^[0-9a-zA-Z\_\/\-\ \']{2,11}$'))
    PRODUCT = ('GP', re.compile('^.*$'), re.compile('^.*$'))
    # Note: COMPOUND is not a type that is allowed in the database!
    COMPOUND = ('CP', re.compile('^C[0-9]{5}$'), re.compile('^[Cc][0-9]{1,5}$'))


class Annotation(models.Model):
    name = models.CharField(max_length=200, unique=True, primary_key=True)

    class AnnotationTypes(models.TextChoices):
        PRODUCT = 'GP', _('Gene Product')
        GENECODE = 'GC', _('Gene Code')
        ORTHOLOG = "OL", _('Ortholog')
        CUSTOM = 'CU', _('Custom Annotation')
        KEGGGENE = 'KG', _('KEGG Gene')
        KEGGREACTION = 'KR', _('KEGG Reaction')
        ENZYMECOMMISSION = 'EC', _('Enzyme Commission')
        GENEONTOLOGY = 'GO', _('Gene Ontology')

    anno_type = models.CharField(
        max_length=2,
        choices=AnnotationTypes.choices
    )

    @property
    def anno_type_verbose(self):
        return self.get_anno_type_display()

    # ensure these things are only calculated once
    _descr = None

    @property
    def description(self) -> str:
        if self._descr:
            return self._descr
        else:
            self._descr = '-'
        if self.anno_type == self.AnnotationTypes.KEGGGENE.value:
            self._descr = self._get_description_from_file(filename='ko.tsv', query=self.name)
        elif self.anno_type == self.AnnotationTypes.KEGGREACTION.value:
            self._descr = self._get_description_from_file(filename='rn.tsv', query=self.name)
        elif self.anno_type == self.AnnotationTypes.ORTHOLOG.value:
            self._descr = self._get_description_from_file(filename='orthologs.tsv', query=self.name)
        elif self.anno_type == self.AnnotationTypes.GENEONTOLOGY.value:
            self._descr = self._get_description_from_file(filename='go.obo', query=self.name)
        return self._descr

    def __str__(self):
        return self.name

    @property
    def html(self):
        return F'<div class="annotation ogb-tag" data-annotype="{self.anno_type}" data-toggle="tooltip" title="{self.description}">{self.name}</div>'

    @staticmethod
    def get_auto_description(query: str):
        if AnnotationRegex.COMPOUND.match_regex.match(query):
            return Annotation._get_description_from_file(
                filename='compound.tsv', query=query.upper())
        if AnnotationRegex.ENZYMECOMMISSION.match_regex.match(query):
            return '-'
        if AnnotationRegex.KEGGGENE.match_regex.match(query):
            return Annotation._get_description_from_file(
                filename='ko.tsv', query=query.upper())
        if AnnotationRegex.KEGGREACTION.match_regex.match(query):
            return Annotation._get_description_from_file(
                filename='rn.tsv', query=query.upper())
        if AnnotationRegex.GENEONTOLOGY.match_regex.match(query):
            return Annotation._get_description_from_file(
                filename='go.obo', query=query.upper())
        if AnnotationRegex.ORTHOLOG.match_regex.match(query):
            return Annotation._get_description_from_file(
                filename='orthologs.tsv', query=query.upper())
        if AnnotationRegex.CUSTOM.match_regex.match(query):
            return '-'
        if AnnotationRegex.GENECODE.match_regex.match(query):
            return '-'

        return '--'

    @staticmethod
    def invariant():
        return len(Annotation.objects.filter(name__contains=',')) == 0 and \
               len(Annotation.objects.filter(name__contains=';')) == 0

    @staticmethod
    def _get_description_from_file(filename: str, query: str):
        if filename == 'go.obo':
            try:
                return gene_ontology.search(query=query)
            except KeyError:
                return '-'

        assert filename in FILENAME_SETTINGS.keys(), F'Supported filenames: {FILENAME_SETTINGS.keys()}. You provided: {filename}'

        prefix = FILENAME_SETTINGS[filename][0]
        file_path = FILENAME_SETTINGS[filename][1]

        try:
            with BinaryFileSearch(file=file_path, sep="\t", string_mode=True) as bfs:
                return_value = bfs.search(query=F"{prefix}{query}")[0][1]
        except (FileNotFoundError, KeyError):
            # When file does not exist.
            return '-'
        except Annotation.DoesNotExist:
            return '-'

        return return_value

    @staticmethod
    def get_annotation_type(query: str):
        for anno_regex in AnnotationRegex:
            if anno_regex.start_regex.match(query):
                return anno_regex.value

        raise Annotation.DoesNotExist(F"Annotation doesn't match any type! '{query}'!")

    @staticmethod
    def load_ortholog_annotations():
        import os
        from website.models import GenomeContent, Gene

        file = settings.ORTHOLOG_ANNOTATIONS['ortholog_to_gene_ids']
        assert os.path.isfile(file), F'Could not load ortholog annotation: {file}'

        print(F'Step 1/5: Deleting all ortholog-annotations.', end=' ', flush=True)
        Annotation.objects.filter(anno_type='OL').delete()

        print(F'Step 2/5: Importing ortholog-annotations from {file}.', end=' ', flush=True)

        all_genomecontent_ids = set(GenomeContent.objects.all().values_list('identifier', flat=True))
        all_genes = set(Gene.objects.all().values_list('identifier', flat=True))
        orthogroups = []
        genomecontent_to_ortholog_links = []
        gene_to_ortholog_links = []

        with open(file) as f:
            for line in f:
                orthogroup, gene_ids = line.rstrip().split('\t', maxsplit=1)
                gene_ids = [gid.rsplit('|', maxsplit=1)[-1] for gid in gene_ids.split('\t')]
                genome_ids = set(gid.rsplit('_')[-1] for gid in gene_ids)

                orthogroup.append(Annotation(name=orthogroup, anno_type='OL'))

                gene_to_ortholog_links.extend(
                    [
                        Gene.annotations.through(gene_id=gene_id, annotation_id=orthogroup)
                        for gene_id in gene_ids
                        if gene_id in all_genes
                    ]
                )

                genomecontent_to_ortholog_links.extend(
                    [
                        GenomeContent.annotations.through(genomecontent_id=genome_id, annotation_id=orthogroup)
                        for genome_id in genome_ids
                        if genome_id in all_genomecontent_ids
                    ]
                )

        # Create Annotation-Objects
        print(F'Step 3/5: Add {len(orthogroups)} orthogroup-annotations to database.', end=' ', flush=True)
        Annotation.objects.bulk_create(orthogroups)

        # Create many-to-many relationships
        print(F'Step 4/5: Link {len(genomecontent_to_ortholog_links)} orthogroup-annotations to genomes.', end=' ', flush=True)
        GenomeContent.annotations.through.objects.bulk_create(genomecontent_to_ortholog_links)
        print(F'Step 5/5: Link {len(gene_to_ortholog_links)} orthogroup-annotations to genes.', end=' ', flush=True)
        Gene.annotations.through.objects.bulk_create(gene_to_ortholog_links)

        print('Success.')
