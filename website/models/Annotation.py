import os
import re
from django.db import models
from django.utils.translation import gettext_lazy as _
from lib.gene_ontology.gene_ontology import GeneOntology
from enum import Enum
import cdblib
from OpenGenomeBrowser import settings

gene_ontology = GeneOntology()


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
    ORTHOLOG = ('OL', re.compile('^((N[0-9]+\.)?H)?OG[0-9]{7}$'), re.compile('^[Oo][Gg][0-9]{1,7}$'))
    GENECODE = ('GC', re.compile('^[0-9a-zA-Z\_\/\-\ \']{3,11}$'), re.compile('^[0-9a-zA-Z\_\/\-\ \']{2,11}$'))
    PRODUCT = ('GP', re.compile('^.*$'), re.compile('^.*$'))
    # Note: COMPOUND is not a type that is allowed in the database!
    COMPOUND = ('CP', re.compile('^C[0-9]{5}$'), re.compile('^[Cc][0-9]{1,5}$'))


class AnnotationDescriptionFile:
    def __init__(self, anno_type: str, create_cdb: bool = True):
        self.anno_type = anno_type
        self.file = f'{settings.ANNOTATION_DESCRIPTIONS}/{anno_type}.tsv'
        if not os.path.isfile(self.file):
            raise FileNotFoundError(f'AnnotationDescriptionFile does not exist: {self.file}')
        self.cdb = f'{self.file}.cdb'
        if not os.path.isfile(self.cdb) or create_cdb:
            self.mk_cdb(self.file, self.cdb)
        self.cdb_reader = self.get_cdb(self.cdb)

    def get_description_or_alternative(self, query: str, alternative='-') -> str:
        try:
            return self.cdb_reader.get(query.encode('utf-8')).decode('utf-8')
        except Exception as e:
            return alternative

    def get_description(self, query: str) -> str:
        return self.cdb_reader.get(query.encode('utf-8')).decode('utf-8')

    def update_descriptions(self, chunk_size=1000, reload=True) -> None:
        if reload:
            queryset = Annotation.objects.filter(anno_type=self.anno_type)
        else:
            queryset = Annotation.objects.filter(anno_type=self.anno_type, description=None)

        for chunk in self.chunked_queryset(queryset, chunk_size=chunk_size):
            for anno in chunk:
                anno.description = self.get_description_or_alternative(anno.name)
            Annotation.objects.bulk_update(objs=chunk, fields=['description'])

    @staticmethod
    def chunked_queryset(queryset, chunk_size=1000):
        """ Slice a queryset into chunks. """

        start_pk = 0
        queryset = queryset.order_by('pk')

        while True:
            # No entry left
            if not queryset.filter(pk__gt=start_pk).exists():
                break

            try:
                # Fetch chunk_size entries if possible
                end_pk = queryset.filter(pk__gt=start_pk).values_list(
                    'pk', flat=True)[chunk_size - 1]

                # Fetch rest entries if less than chunk_size left
            except IndexError:
                end_pk = queryset.values_list('pk', flat=True).last()

            yield queryset.filter(pk__gt=start_pk).filter(pk__lte=end_pk)

            start_pk = end_pk

    @staticmethod
    def mk_cdb(file: str, cdb: str) -> None:
        with open(file) as in_f, open(cdb, 'wb') as out_f, cdblib.Writer(out_f) as writer:
            for line in in_f.readlines():
                k, v = line.strip().split('\t')
                writer.put(k.encode('utf-8'), v.encode('utf-8'))

    @staticmethod
    def get_cdb(cdb: str) -> cdblib.Reader:
        reader = cdblib.Reader.from_file_path(cdb)
        return reader


class Annotation(models.Model):
    name = models.CharField(max_length=200, unique=True, primary_key=True)
    description = models.TextField(blank=True)

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

    def __str__(self):
        return self.name

    @property
    def html(self):
        return F'<div class="annotation ogb-tag" data-annotype="{self.anno_type}" title="{self.description}">{self.name}</div>'

    @staticmethod
    def invariant():
        return len(Annotation.objects.filter(name__contains=',')) == 0 and \
               len(Annotation.objects.filter(name__contains=';')) == 0

    @staticmethod
    def load_descriptions(anno_types: list = None, reload=True):
        if anno_types is None:
            anno_types = list(Annotation.objects.distinct('anno_type').values_list('anno_type', flat=True))  # ['EC', 'GC', 'GO', 'GP', 'KG', 'KR']

        if reload:
            print('Reloading annotation descriptions...')
        else:
            print('Loading missing descriptions...')

        for anno_type in anno_types:
            try:
                adf = AnnotationDescriptionFile(anno_type=anno_type, create_cdb=reload)
                print(f'Loading {adf.file}...')
                adf.update_descriptions(reload=reload)
            except FileNotFoundError:
                print(f'Annotation-description file does not exist: {settings.ANNOTATION_DESCRIPTIONS}/{anno_type}.tsv')

    @staticmethod
    def load_ortholog_annotations():
        from website.models import GenomeContent, Gene

        assert os.path.isfile(settings.ORTHOLOG_ANNOTATIONS), F'File does not exist: {settings.ORTHOLOG_ANNOTATIONS}'

        print(F'Step 1/5: Deleting all ortholog-annotations.', end=' ', flush=True)
        Annotation.objects.filter(anno_type='OL').delete()

        print(F'Step 2/5: Importing ortholog-annotations from {settings.ORTHOLOG_ANNOTATIONS}.', end=' ', flush=True)

        all_genomecontent_ids = set(GenomeContent.objects.all().values_list('identifier', flat=True))
        all_genes = set(Gene.objects.all().values_list('identifier', flat=True))
        orthogroups = []
        genomecontent_to_ortholog_links = []
        gene_to_ortholog_links = []

        try:
            adf = AnnotationDescriptionFile('OL', create_cdb=True)

            def get_descr(query):
                return adf.get_description_or_alternative(query, alternative='-')
        except FileNotFoundError:
            def get_descr(query):
                return '-'

        with open(settings.ORTHOLOG_ANNOTATIONS) as f:
            for line in f:
                orthogroup, gene_ids = line.rstrip().split('\t', maxsplit=1)
                gene_ids = [gid.rsplit('|', maxsplit=1)[1] for gid in gene_ids.split(', ')]
                genome_ids = set(gid.rsplit('_', maxsplit=1)[0] for gid in gene_ids)

                orthogroups.append(Annotation(name=orthogroup, anno_type='OL', description=get_descr(orthogroup)))

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
