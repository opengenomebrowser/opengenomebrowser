import os
import re
import json
from django.db import models
import cdblib
from OpenGenomeBrowser import settings


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
            queryset = Annotation.objects.filter(anno_type=self.anno_type, description='')

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


class AnnotationType:
    def __init__(self, anno_type: str, data: dict):
        self._raw: dict = data
        self.anno_type: str = anno_type
        self.name: str = data['name']
        self.color: str = data['color']
        self.regex: re.Pattern = re.compile(data['regex'])
        self.hyperlinks: list = data['hyperlinks']

        for hyperlink in self.hyperlinks:
            for key in ['url', 'name']:
                assert key in hyperlink and type(hyperlink[key]) is str, self

    def __repr__(self) -> str:
        return f'<AnnotationType {self.anno_type}>'

    @property
    def css(self):
        return f'[data-annotype="{self.anno_type}"] {{background-color: {self.color} !important; color: black !important}}'


with open(f'{settings.GENOMIC_DATABASE}/annotations.json') as f:
    annotation_types = {anno_type: AnnotationType(anno_type, data) for anno_type, data in json.load(f).items()}


class Annotation(models.Model):
    name = models.TextField(unique=True, primary_key=True)
    description = models.TextField(blank=True)

    anno_type = models.CharField(max_length=2)

    @property
    def anno_type_verbose(self):
        return annotation_types[self.anno_type].name

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
               len(Annotation.objects.filter(name__contains=';')) == 0, \
               'Some annotations contain invalid characers: , or :'

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
    def load_ortholog_annotations(batch_size: int = 5000):
        from website.models import GenomeContent, Gene

        assert os.path.isfile(settings.ORTHOLOG_ANNOTATIONS), F'File does not exist: {settings.ORTHOLOG_ANNOTATIONS}'

        print(F'Step 1: Deleting all ortholog-annotations.')
        Annotation.objects.filter(anno_type='OL').delete()

        print(F'Step 2: Importing ortholog-annotations from {settings.ORTHOLOG_ANNOTATIONS}.')

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
            for line_nr, line in enumerate(f, 1):
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

                if line_nr % batch_size == 0:
                    print(F'Step 3, batch {line_nr // batch_size}:', end=' ', flush=True)
                    # Create Annotation-Objects
                    print(F'+{len(orthogroups)} orthogroups', end=' ', flush=True)
                    Annotation.objects.bulk_create(orthogroups)

                    # Create many-to-many relationships
                    print(F'+{len(genomecontent_to_ortholog_links)} orthogroups-to-genomes.', end=' ', flush=True)
                    GenomeContent.annotations.through.objects.bulk_create(genomecontent_to_ortholog_links)

                    print(F'+{len(gene_to_ortholog_links)} orthogroups-to-genes.')
                    Gene.annotations.through.objects.bulk_create(gene_to_ortholog_links)

                    orthogroups = []
                    genomecontent_to_ortholog_links = []
                    gene_to_ortholog_links = []

        print('Success.')

    @staticmethod
    def get_annotype_css_paths():
        files = [
            os.path.abspath(F'{settings.BASE_DIR}/website/static/global/css/annotype_color.css'),
            os.path.abspath(F'{settings.BASE_DIR}/static_root/global/css/annotype_color.css')
        ]
        for file in files:
            # ensure parent folder exists
            os.makedirs(os.path.dirname(file), exist_ok=True)
        return files

    @staticmethod
    def create_annotype_color_css():
        css = ['[data-annotype="fake"] {background-color: lightgrey !important; color: black !important}']
        for anno_type in annotation_types.values():
            css.append(anno_type.css)

        for file in Annotation.get_annotype_css_paths():
            with open(file, 'w') as f:
                f.write('\n'.join(css))
