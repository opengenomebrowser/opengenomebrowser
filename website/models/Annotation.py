from django.db import models
from django.utils.translation import gettext_lazy as _
from binary_file_search.BinaryFileSearch import BinaryFileSearch
from lib.orthofinder_tools.orthogroup_to_gene_name import OrthogroupToGeneName
from enum import Enum
import re
from django.core.exceptions import ValidationError
from OpenGenomeBrowser import settings


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
    ORTHOLOG = ('OL', re.compile('^OG[0-9]{7}$'), re.compile('^[Oo][Gg][0-9]{1,7}$'))
    GENECODE = ('GC', re.compile('^[0-9a-zA-Z\_\/\-\ \']{3,11}$'), re.compile('^[0-9a-zA-Z\_\/\-\ \']{2,11}$'))
    PRODUCT = ('GP', re.compile('^.*$'), re.compile('^.*$'))
    # Note: COMPOUND is not a type that is allowed in the database!
    COMPOUND = ('CP', re.compile('^C[0-9]{5}$'), re.compile('^[Cc][0-9]{1,5}$'))


# todo: this doesn't work!
# def validate_annotation_name(name: str):
#     if ',' in name or ';' in name:
#         raise ValidationError(F"Annotation names may not contain ',' or ';'. Problem occurred here: {name}")


class Annotation(models.Model):
    name = models.CharField(max_length=200, unique=True, primary_key=True)

    class AnnotationTypes(models.TextChoices):
        GENECODE = 'GC', _('Gene Code')
        CUSTOM = 'CU', _('Custom Annotation')
        ENZYMECOMMISSION = 'EC', _('Enzyme Commission Number')
        KEGGGENE = 'KG', _('Kegg Gene')
        KEGGREACTION = 'KR', _('Kegg Reaction')
        GENEONTOLOGY = 'GO', _('Gene Ontology Number')
        ORTHOLOG = "OL", _('Ortholog')
        PRODUCT = 'GP', _('Gene Product')

    anno_type = models.CharField(
        max_length=2,
        choices=AnnotationTypes.choices
    )

    @property
    def anno_type_verbose(self):
        return self.get_anno_type_display()

    @property
    def description(self) -> str:
        if self.anno_type == self.AnnotationTypes.KEGGGENE.value:
            return self._get_description_from_file(filename='ko.tsv', query=self.name)
        if self.anno_type == self.AnnotationTypes.KEGGREACTION.value:
            return self._get_description_from_file(filename='rn.tsv', query=self.name)
        if self.anno_type == self.AnnotationTypes.ORTHOLOG.value:
            return self._get_description_from_file(filename='Orthogroup_BestNames.tsv', query=self.name)
        return '-'

    @property
    def anno_html(self):
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
            return '-'
        if AnnotationRegex.ORTHOLOG.match_regex.match(query):
            return Annotation._get_description_from_file(
                filename='Orthogroup_BestNames.tsv', query=query.upper())
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
        filename_settings = {
            'ko.tsv': ('ko:', 'lib/custom_kegg/data/rest_data/ko.tsv'),
            'rn.tsv': ('rn:', 'lib/custom_kegg/data/rest_data/rn.tsv'),
            'compound.tsv': ('cpd:', 'lib/custom_kegg/data/rest_data/rn.tsv'),
            'Orthogroup_BestNames.tsv': ('', F'{settings.GENOMIC_DATABASE}/OrthoFinder/Orthogroup_BestNames.tsv')
        }
        assert filename in filename_settings.keys(), F'Supported filenames: {filename_settings.keys()}. You provided: {filename}'

        prefix = filename_settings[filename][0]
        file_path = filename_settings[filename][1]

        try:
            with BinaryFileSearch(file=file_path, sep="\t", string_mode=True) as bfs:
                return_value = bfs.search(query=F"{prefix}{query}")[0][1]
        except FileNotFoundError:
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
    def reload_orthofinder():
        import os
        from . import Genome, Gene

        orthofinder_base = F'{settings.GENOMIC_DATABASE}/OrthoFinder/'

        with open(F'{orthofinder_base}/orthofinder_folder.txt') as f:
            orthofinder_folder = f.read().strip()

        fastas_path = orthofinder_base + 'fastas/'
        orthogroups_dir = fastas_path + F'OrthoFinder/{orthofinder_folder}/Orthogroups/'
        orthogroups_txt = orthogroups_dir + 'Orthogroups.txt'
        orthogroups_tsv = orthogroups_dir + 'Orthogroups.tsv'
        orthogroups_best_names = orthogroups_dir + 'Orthogroup_BestNames.tsv'
        orthogroups_best_names_symlink = orthofinder_base + 'Orthogroup_BestNames.tsv'

        print('Deleting all orthogroup-annotations.')
        Annotation.objects.filter(anno_type='OL').delete()
        if os.path.isfile(orthogroups_best_names_symlink):
            os.unlink(orthogroups_best_names_symlink)

        if not os.path.isfile(orthogroups_txt):
            print("No Orthogroups.txt specified. (This is not obligatory. To add one, save it here: {})".format(
                orthogroups_txt))
            return

        print('Importing OrthoFinder/Orthogroups. Step 1/5: Read Orthogroups.txt.', end=' ', flush=True)

        with open(orthogroups_txt, 'r') as f:
            line = f.readline().strip()

            all_genomes = set(Genome.objects.all().values_list('identifier', flat=True))
            all_genes = set(Gene.objects.all().values_list('identifier', flat=True))
            orthogroups = []
            genome_to_ortholog_links = []
            gene_to_ortholog_links = []
            while line:
                orthogroup, gene_identifiers = line.split(': ', maxsplit=1)
                gene_identifiers = [s.rsplit('|', maxsplit=1)[-1] for s in gene_identifiers.split(" ")]
                strains = [gene_id.split("_", maxsplit=1)[0] for gene_id in gene_identifiers]

                if len(strains) == 1:
                    break

                orthogroups.append(orthogroup)

                for gene_id in gene_identifiers:
                    if gene_id in all_genes:
                        gene_to_ortholog_links.append(
                            Gene.annotations.through(gene_id=gene_id, annotation_id=orthogroup))

                for strain in set(strains):
                    if strain in all_genomes:
                        genome_to_ortholog_links.append(
                            Genome.annotations.through(genome_id=strain, annotation_id=orthogroup))

                line = f.readline().strip()

        # Create Annotation-Objects
        print('Step 2/5: Add orthogroup-annotations to database.', end=' ', flush=True)
        Annotation.objects.bulk_create([Annotation(name=group, anno_type='OL') for group in orthogroups])

        # Create many-to-many relationships
        print('Step 3/5: Link orthogroup-annotations to genomes.', end=' ', flush=True)
        Genome.annotations.through.objects.bulk_create(genome_to_ortholog_links)
        print('Step 4/5: Link orthogroup-annotations to genes.', end=' ', flush=True)
        Gene.annotations.through.objects.bulk_create(gene_to_ortholog_links)

        print('Step 5/5: Create Orthogroup_BestNames.tsv.', end=' ', flush=True)
        OrthogroupToGeneName.run(orthogroups_tsv=orthogroups_tsv, fasta_dir=fastas_path, write=True)
        if os.path.islink(orthogroups_best_names_symlink):
            os.remove(orthogroups_best_names_symlink)
        os.symlink(os.path.abspath(orthogroups_best_names), orthogroups_best_names_symlink)

        print('Success.')
