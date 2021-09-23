from django.db.models.manager import Manager
from hashlib import sha224
from django.db import models
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField
from .Organism import Organism
from .TaxID import TaxID
from .Tag import Tag
from .GenomeContent import GenomeContent
from OpenGenomeBrowser import settings
from functools import cached_property
from website.models.helpers.backup_file import read_file_or_default, overwrite_with_backup
from website.models.helpers import AnnotatedGenomeManager


class Genome(models.Model):
    """
    Represents a measurement of a organism.

    Imported from database/genomes/organism/genomes/*
    """

    """
    todo: ensure tags are imported, and saved to metadata if changed through admin
    """
    objects = Manager()
    annotated_objects = AnnotatedGenomeManager()

    # MANDATORY general information about the isolate
    identifier = models.CharField('Unique identifier', max_length=50, unique=True)
    organism = models.ForeignKey(Organism, on_delete=models.CASCADE, null=True, blank=True)
    genomecontent = models.OneToOneField(GenomeContent, on_delete=models.CASCADE, null=True, blank=True)

    tags = models.ManyToManyField(Tag, blank=True)
    contaminated = models.BooleanField('Contaminated?', default=False)
    old_identifier = models.CharField('Old identifier', max_length=50, null=True, blank=True)

    # information about isolation
    isolation_date = models.DateField('Isolation date', null=True, blank=True)
    env_broad_scale = ArrayField(models.TextField(), verbose_name='Broad isolation environment', default=list, blank=True)
    env_local_scale = ArrayField(models.TextField(), verbose_name='Local isolation environment', default=list, blank=True)
    env_medium = ArrayField(models.TextField(), verbose_name='Environment medium', default=list, blank=True)
    growth_condition = models.CharField('Growth condition', max_length=100, null=True, blank=True)
    geographical_coordinates = models.CharField('Geographical coordinates', max_length=200, null=True, blank=True)
    geographical_name = models.CharField('Geographical name', max_length=50, null=True, blank=True)

    # information about sequencing
    library_preparation = models.CharField('Library Preparation', max_length=40, null=True, blank=True)
    sequencing_tech = models.CharField('Sequencing technology', max_length=40, null=True, blank=True)
    sequencing_tech_version = models.CharField('Sequencing technology version', max_length=20, null=True, blank=True)
    sequencing_date = models.DateField('Sequencing date', null=True, blank=True)
    read_length = models.CharField('Read length', max_length=8, null=True, blank=True)
    sequencing_coverage = models.CharField('Sequencing coverage', max_length=8, null=True, blank=True)

    # information about assembly
    assembly_tool = models.CharField('Assembly tool', max_length=40, null=True, blank=True)
    assembly_version = models.CharField('Assembly version', max_length=40, null=True, blank=True)
    assembly_date = models.DateField('Assembly date', null=True, blank=True)

    assembly_fasta_file = models.CharField(max_length=200)
    assembly_gc = models.FloatField('GC content', null=True, blank=True)
    assembly_longest_scf = models.IntegerField('Longest scaffold', null=True, blank=True)
    assembly_size = models.IntegerField('Assembly size', null=True, blank=True)
    assembly_nr_scaffolds = models.IntegerField('Number of scaffolds', null=True, blank=True)
    assembly_n50 = models.IntegerField('N50', null=True, blank=True)
    assembly_gaps = models.IntegerField('Number of gaps', null=True, blank=True)
    assembly_ncount = models.IntegerField('Total Ns', null=True, blank=True)
    nr_replicons = models.IntegerField('Number of replicons', null=True, blank=True)

    # contamination analysis
    custom_tables = JSONField(default=list, blank=True, null=True)

    # information about CDS prediction
    cds_tool = models.CharField('Primary annotation tool', max_length=50, null=True, blank=True)
    cds_tool_date = models.DateField('Date of primary annotation', null=True, blank=True)
    cds_tool_version = models.CharField('Version of primary annotation', max_length=20, null=True, blank=True)
    cds_tool_faa_file = models.CharField(max_length=200)  # MANDATORY
    cds_tool_gbk_file = models.CharField(max_length=200)  # MANDATORY
    cds_tool_gff_file = models.CharField(max_length=200)  # MANDATORY
    cds_tool_ffn_file = models.CharField(max_length=200, null=True, blank=True)
    cds_tool_sqn_file = models.CharField(max_length=200, null=True, blank=True)

    BUSCO = JSONField(default=dict)  # {C:2,D:2,F:2,M:2,S:2,T:2]}  +  {dataset: firmicutes_odb9}  +  {dataset_creation_date: "2000-01-31"}
    BUSCO_percent_single = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    COG = JSONField(default=dict)  # {'J': 152.5, 'A': 2, 'K': 29.333, ... }

    # information about annotation
    custom_annotations = JSONField(default=list, blank=True, null=True)  # [{"date": "2016-02-29", "file": "FAM19038.ko", "type": "KG"}]

    # accession numbers if the genome has been published
    bioproject_accession = models.CharField('Bioproject accession', max_length=20, null=True, blank=True)
    biosample_accession = models.CharField('Biosample accession', max_length=20, null=True, blank=True)
    genome_accession = models.CharField('Genome accession', max_length=20, null=True, blank=True)

    # literature references
    literature_references = JSONField('Literature references', default=list, blank=True, null=True)

    def __str__(self):
        return self.identifier

    def natural_key(self):
        return self.identifier

    @property
    def parent(self):
        return self.taxid

    def set_representative(self):
        self.organism.set_representative(self)

    @property
    def taxid(self) -> TaxID:
        return self.organism.taxid

    @property
    def taxscientificname(self):
        return self.taxid.taxscientificname

    @property
    def html(self):
        classes = ['genome', 'ogb-tag']
        if not self.is_representative:
            classes.append('no-representative')
        if self.contaminated:
            classes.append('contaminated')
        if self.restricted:
            classes.append('restricted')
        return f'<span class="{" ".join(classes)}" data-species="{self.taxid.taxscientificname}">{self.identifier}</span>'

    @property
    def html_warning_stripes(self):
        classes = []
        print(self, self.is_representative)
        if not self.is_representative:
            classes.append('no-representative')
        if self.contaminated:
            classes.append('contaminated')
        if self.restricted:
            classes.append('restricted')

        return ' '.join(classes)

    @property
    def is_representative(self) -> bool:
        return hasattr(self, 'representative') and self.representative is not None

    @property
    def restricted(self) -> bool:
        return self.organism.restricted

    @property
    def genomecontent__n_genes(self) -> int:
        return self.genomecontent.n_genes

    def base_path(self, relative=True) -> str:
        rel = F"organisms/{self.organism.name}/genomes/{self.identifier}"
        return rel if relative else f'{settings.GENOMIC_DATABASE}/{rel}'

    def assembly_fasta(self, relative=True) -> str:  # mandatory
        return F"{self.base_path(relative)}/{self.assembly_fasta_file}"

    def cds_faa(self, relative=True) -> str:  # mandatory
        return F"{self.base_path(relative)}/{self.cds_tool_faa_file}"

    def cds_gbk(self, relative=True) -> str:  # mandatory
        return F"{self.base_path(relative)}/{self.cds_tool_gbk_file}"

    def cds_gff(self, relative=True) -> str:  # mandatory
        return F"{self.base_path(relative)}/{self.cds_tool_gff_file}"

    def cds_ffn(self, relative=True) -> str:
        if not self.cds_tool_ffn_file:
            return None
        return F"{self.base_path(relative)}/{self.cds_tool_ffn_file}"

    def cds_sqn(self, relative=True) -> str:
        if not self.cds_tool_sqn_file:
            return None
        return F"{self.base_path(relative)}/{self.cds_tool_sqn_file}"

    @cached_property
    def all_tags(self):
        return (self.tags.all() | self.organism.tags.all()).distinct()

    @property
    def metadata_json(self) -> str:
        return f'{settings.GENOMIC_DATABASE}/organisms/{self.organism.name}/genomes/{self.identifier}/genome.json'

    def markdown_path(self, relative=True) -> str:
        return F"{self.base_path(relative)}/genome.md"

    def markdown(self, default=None) -> str:
        return read_file_or_default(file=self.markdown_path(relative=False), default=default, default_if_empty=True)

    def set_markdown(self, md: str, user: str = None):
        overwrite_with_backup(file=self.markdown_path(relative=False), content=md, user=user, delete_if_empty=True)

    @staticmethod
    def hash_genomes(genomes) -> str:
        identifiers = sorted(set(g.identifier for g in genomes))
        identifier_string = ' '.join(identifiers)
        hash = sha224(identifier_string.encode('utf-8')).hexdigest()
        assert len(hash) == 56
        return hash

    def invariant(self):
        from website.serializers import GenomeSerializer
        from db_setup.check_metadata import genome_metadata_is_valid
        from db_setup.FolderLooper import MockGenome, MockOrganism

        assert self.identifier.startswith(self.organism.name)

        # ensure metadata is valid
        g_s_g = GenomeSerializer(self)
        genome_state = g_s_g.data
        assert genome_metadata_is_valid(genome_state, path_to_genome=self.base_path(relative=False), raise_exception=True)

        # ensure metadata json matches genome
        m_o = MockOrganism(path=self.organism.base_path(relative=False))
        m_g = MockGenome(path=self.base_path(relative=False), organism=m_o)
        matches, differences = GenomeSerializer.json_matches_genome(genome=self, json_dict=m_g.json, organism_name=self.organism.name)
        assert matches, f'json and database do not match. organism: {self.identifier} differences: {differences}'

        return True

    @cached_property
    def get_tag_html(self) -> str:
        tags = (self.tags.all() | self.organism.tags.all()).distinct()
        html = [tag.get_html_badge() for tag in tags.order_by('tag')]
        return " ".join(html)

    @staticmethod
    def is_valid_date(date_string: str) -> bool:
        from datetime import datetime
        try:
            datetime.strptime(date_string, "%Y-%m-%d")
            return True
        except ValueError:
            print("Invalid date string:", date_string)
            return False

    @staticmethod
    def is_valid_reference(reference: str) -> bool:
        """ :returns: true if valid PMID, DOI or URL """

        from urllib.parse import urlparse
        isurl = urlparse(reference, scheme='http')
        if all([isurl.scheme, isurl.netloc, isurl.path]):
            return True  # is valid URL

        import re
        if re.match("(^[0-9]{8}$)|(^10.[0-9]{4,9}/[-._;()/:A-Za-z0-9]+$)", reference):
            return True  # is valid PMID, DOI
        print("Invalid reference in {}: '{}'. Is neither URL, PMID or DOI!".format(reference))
        return False

    def save(self, *args, **kwargs):
        genomecontent, created = GenomeContent.objects.get_or_create(identifier=self.identifier)
        self.genomecontent = genomecontent
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.genomecontent.delete()
        super().delete(*args, **kwargs)

    def update_assembly_info(self):
        if self.assembly_fasta:
            # calculate GC-content
            from Bio import SeqIO
            from Bio.SeqUtils import GC
            gc = {(GC(record.seq), len(record)) for record in SeqIO.parse(self.assembly_fasta(relative=False), "fasta")}
            gc_times_len = sum([gc_content * length for gc_content, length in gc])
            total_assembly_length = sum([length for gc_content, length in gc])
            self.assembly_gc = round(gc_times_len / total_assembly_length, 1)
            assert 0 <= self.assembly_gc <= 100, f'{self} :: assembly gc content is beyond reasonable bounds! {self.assembly_gc}'

            # calculate assembly-stats
            from lib.assembly_stats.assembly_stats import AssemblyStats
            assembly_stats = AssemblyStats().get_assembly_stats(self.assembly_fasta(relative=False))
            self.assembly_longest_scf = assembly_stats['longest']
            self.assembly_size = assembly_stats['total_length']
            self.assembly_nr_scaffolds = assembly_stats['number']
            self.assembly_n50 = assembly_stats['N50']
            self.assembly_gaps = assembly_stats['Gaps']
            self.assembly_ncount = assembly_stats['N_count']
            self.save()

    @staticmethod
    def is_valid_env(envs):
        for env in envs:
            if env[:5] == 'ENVO:' and int(env[5:]) > 0 and len(env) == 13:
                return True
            if env[:7] == 'FOODON:' and int(env[7:]) > 0 and len(env) == 15:
                return True
            print(F"Poorly formatted env: {env}")
            return False
        return True
