from django.db import models
from django.db.models import JSONField
from .Organism import Organism
from .TaxID import TaxID
from .Tag import Tag
from .GenomeContent import GenomeContent
import os
from OpenGenomeBrowser import settings
from functools import cached_property


class Genome(models.Model):
    """
    Represents a measurement of a organism.

    Imported from database/genomes/organism/genomes/*
    """

    # MANDATORY general information about the isolate
    identifier = models.CharField('Unique identifier', max_length=50, unique=True)
    organism = models.ForeignKey(Organism, on_delete=models.CASCADE, null=True, blank=True)
    genomecontent = models.OneToOneField(GenomeContent, on_delete=models.CASCADE, null=True, blank=True)

    tags = models.ManyToManyField(Tag, blank=True)
    contaminated = models.BooleanField('Contaminated?', default=False)
    old_identifier = models.CharField('Old identifier', max_length=50, null=True, blank=True)

    # information about isolation
    isolation_date = models.DateField('Isolation date', null=True, blank=True)
    env_broad_scale = JSONField(default=list, blank=True, null=True)
    env_local_scale = JSONField(default=list, blank=True, null=True)
    env_medium = JSONField(default=list, blank=True, null=True)
    growth_condition = models.CharField('Growth vondition', max_length=100, null=True, blank=True)
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
    assembly_longest_scf = models.IntegerField('Longest scaffold', null=True, blank=True)
    assembly_size = models.IntegerField('Assembly size', null=True, blank=True)
    assembly_nr_scaffolds = models.IntegerField('Number of scaffolds', null=True, blank=True)
    assembly_n50 = models.IntegerField('N50', null=True, blank=True)
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
    BUSCO_percent_single = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    # format(self.BUSCO['S'] / self.BUSCO['T'], ".1%")

    # information about annotation
    custom_annotations = JSONField(default=list, blank=True, null=True)  # [{"date": "2016-02-29", "file": "FAM19038.ko", "type": "KEGG"}]

    # accession numbers if the genome has been published
    bioproject_accession = models.CharField(max_length=20, null=True, blank=True)
    biosample_accession = models.CharField(max_length=20, null=True, blank=True)
    genome_accession = models.CharField(max_length=20, null=True, blank=True)

    # literature references
    literature_references = JSONField(default=list, blank=True, null=True)  # ["ref1", "ref2",]

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
        return F'<div class="genome ogb-tag" data-species="{self.taxid.taxscientificname}" data-toggle="tooltip">{self.identifier}</div>'

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
        if relative:
            return rel
        else:
            return F"{settings.GENOMIC_DATABASE}/{rel}"

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
    def metadata_json(self):
        return F'{settings.GENOMIC_DATABASE}/organisms/{self.organism.name}/genomes/{self.identifier}/genome.json'

    def __str__(self):
        return self.identifier

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
        assert matches, F'json and database do not match. organism: {self.identifier} differences: {differences}'

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
        self.genomecontent.wipe_data()
        self.genomecontent.delete()
        super().delete(*args, **kwargs)

    def update_assembly_info(self):
        if self.assembly_fasta:
            from lib.assembly_stats.assembly_stats import AssemblyStats
            assembly_stats = AssemblyStats().get_assembly_stats(self.assembly_fasta(relative=False))
            self.assembly_longest_scf = assembly_stats['longest']
            self.assembly_size = assembly_stats['total_length']
            self.assembly_nr_scaffolds = assembly_stats['number']
            self.assembly_n50 = assembly_stats['N50']
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

    @staticmethod
    def get_selector_to_description_dict():
        selector_to_description_dict = {
            'organism.name': {'filter_type': 'text', 'description': 'Organism'},
            'identifier': {'filter_type': 'text', 'description': 'Identifier'},
            'old_identifier': {'filter_type': 'text', 'description': 'Old Identifier'},
            'representative': {'filter_type': 'binary', 'description': 'Representative'},
            'organism.restricted': {'filter_type': 'binary', 'description': 'Restricted'},
            'contaminated': {'filter_type': 'binary', 'description': 'Contaminated'},
            'genome_tags': {'filter_type': 'custom-tags', 'description': 'Genome-Tags'},
            'organism_tags': {'filter_type': 'custom-tags', 'description': 'Organism-Tags'},
            'isolation_date': {'filter_type': 'range_date', 'description': 'Isolation date'},
            'env_broad_scale': {'filter_type': 'no-filter', 'description': 'Broad Isolation Environment'},
            'env_local_scale': {'filter_type': 'no-filter', 'description': 'Local Isolation Environment'},
            'env_medium': {'filter_type': 'no-filter', 'description': 'Environment Medium'},
            'growth_condition': {'filter_type': 'no-filter', 'description': 'Growth Condition'},
            'geographical_coordinates': {'filter_type': 'no-filter', 'description': 'Isolation Coordinates'},
            'geographical_name': {'filter_type': 'no-filter', 'description': 'Geographical Name'},
            'library_preparation': {'filter_type': 'multi_select', 'description': 'Library Preparation'},
            'sequencing_tech': {'filter_type': 'multi_select', 'description': 'Sequencing Technology'},
            'sequencing_tech_version': {'filter_type': 'no-filter', 'description': 'Sequencing Technology Version'},
            'sequencing_date': {'filter_type': 'no-filter', 'description': 'Sequencing Date'},
            'read_length': {'filter_type': 'no-filter', 'description': 'Read Length'},
            'sequencing_coverage': {'filter_type': 'no-filter', 'description': 'Sequencing Coverage'},
            'assembly_tool': {'filter_type': 'no-filter', 'description': 'Assembly Tool'},
            'assembly_version': {'filter_type': 'no-filter', 'description': 'Assembly Tool Version'},
            'assembly_date': {'filter_type': 'no-filter', 'description': 'Assembly Date'},
            'assembly_longest_scf': {'filter_type': 'no-filter', 'description': 'Assembly Longest Scf'},
            'assembly_size': {'filter_type': 'no-filter', 'description': 'Assembly Size'},
            'assembly_nr_scaffolds': {'filter_type': 'no-filter', 'description': 'Assembly #Scfs'},
            'assembly_n50': {'filter_type': 'no-filter', 'description': 'Assembly N50'},
            'nr_replicons': {'filter_type': 'no-filter', 'description': 'Assembly #Replicons'},
            'cds_tool': {'filter_type': 'no-filter', 'description': 'CDS Tool'},
            'cds_tool_version': {'filter_type': 'no-filter', 'description': 'CDS Tool Version'},
            'cds_tool_date': {'filter_type': 'no-filter', 'description': 'CDS Date'},
            'genomecontent__n_genes': {'filter_type': 'no-filter', 'description': 'Number of genes'},
            'BUSCO_percent_single': {'filter_type': 'no-filter', 'description': 'BUSCO [%S]'},
            'bioproject_accession': {'filter_type': 'no-filter', 'description': 'Bioproject'},
            'biosample_accession': {'filter_type': 'no-filter', 'description': 'Biosample'},
            'genome_accession': {'filter_type': 'no-filter', 'description': 'Genome Accession'},
            'literature_references': {'filter_type': 'no-filter', 'description': 'Literature References'},
            'organism.taxid.taxsuperkingdom': {'filter_type': 'multi_select', 'description': 'Superkingdom'},
            'organism.taxid.taxphylum': {'filter_type': 'multi_select', 'description': 'Phylum'},
            'organism.taxid.taxclass': {'filter_type': 'multi_select', 'description': 'Class'},
            'organism.taxid.taxorder': {'filter_type': 'multi_select', 'description': 'Order'},
            'organism.taxid.taxfamily': {'filter_type': 'multi_select', 'description': 'Family'},
            'organism.taxid.taxgenus': {'filter_type': 'multi_select', 'description': 'Genus'},
            'organism.taxid.taxspecies': {'filter_type': 'multi_select', 'description': 'Species'},
            'organism.taxid.taxsubspecies': {'filter_type': 'multi_select', 'description': 'Subspecies'},
            'organism.taxid.taxscientificname': {'filter_type': 'multi_select', 'description': 'Taxonomy'},
            'organism.taxid.id': {'filter_type': 'multi_select', 'description': 'TaxID'}
        }
        return selector_to_description_dict
