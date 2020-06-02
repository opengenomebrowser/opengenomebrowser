from django.db import models
from django.contrib.postgres.fields import JSONField
from .Strain import Strain
from .TaxID import TaxID
from .Tag import Tag
from .Genome import Genome
import os
from OpenGenomeBrowser import settings


class Member(models.Model):
    """
    Represents a measurement of a strain.

    Imported from database/genomes/strain/members/*
    """

    # MANDATORY general information about the isolate
    identifier = models.CharField('Unique Identifier', max_length=50, unique=True)
    strain = models.ForeignKey(Strain, on_delete=models.CASCADE)
    representative = models.OneToOneField(Strain, related_name="representative",
                                          on_delete=models.CASCADE, blank=True, null=True)
    genome = models.OneToOneField(Genome, on_delete=models.CASCADE)

    tags = models.ManyToManyField(Tag)
    contaminated = models.BooleanField('Contaminated?', default=False)
    old_identifier = models.CharField('Old Identifier', max_length=50, null=True, blank=True)

    # information about isolation
    isolation_date = models.DateField('Date of Isolation', null=True, blank=True)
    env_broad_scale = JSONField(default=list)
    env_local_scale = JSONField(default=list)
    env_medium = JSONField(default=list)
    growth_condition = models.CharField('Growth Condition', max_length=100, null=True, blank=True)
    geographical_coordinates = models.CharField('Geographical Coordinates', max_length=200, null=True, blank=True)
    geographical_name = models.CharField('Geographical Name', max_length=50, null=True, blank=True)

    # information about sequencing
    sequencing_tech = models.CharField('Sequencing Technology', max_length=40, null=True, blank=True)
    sequencing_tech_version = models.CharField('Sequencing Technology Version', max_length=20, null=True, blank=True)
    sequencing_date = models.CharField('Date of Sequencing', max_length=30, null=True,
                                       blank=True)  # 2018.01.01//2019.01.01
    sequencing_coverage = models.CharField('Sequencing Coverage', max_length=8, null=True, blank=True)

    # information about assembly
    assembly_tool = models.CharField('Assembly Tool', max_length=40, null=True, blank=True)
    assembly_version = models.CharField('Assembly Version', max_length=40, null=True, blank=True)
    assembly_date = models.CharField('Date of Assembly', max_length=30, null=True, blank=True)  # 2018.01.01//2019.01.01

    assembly_fasta_file = models.CharField(max_length=200)
    assembly_longest_scf = models.IntegerField('Longest Scaffold', null=True, blank=True)
    assembly_size = models.IntegerField('Assembly Size', null=True, blank=True)
    assembly_nr_scaffolds = models.IntegerField('Number of Scaffolds', null=True, blank=True)
    assembly_n50 = models.IntegerField('Assembly N50', null=True, blank=True)
    nr_replicons = models.IntegerField('Number of Replicons', null=True, blank=True)

    # contamination analysis
    origin_included_sequences = JSONField(default=list)
    origin_excluded_sequences = JSONField(default=list)

    # information about CDS prediction
    cds_tool = models.CharField('Primary Annotation Tool', max_length=50, null=True, blank=True)
    cds_tool_date = models.DateField('Date of Primary Annotation', null=True, blank=True)
    cds_tool_version = models.CharField('Version of Primary Annotation', max_length=20, null=True, blank=True)
    cds_tool_faa_file = models.CharField(max_length=200)  # MANDATORY
    cds_tool_gbk_file = models.CharField(max_length=200)  # MANDATORY
    cds_tool_gff_file = models.CharField(max_length=200)  # MANDATORY
    cds_tool_ffn_file = models.CharField(max_length=200, null=True, blank=True)
    cds_tool_sqn_file = models.CharField(max_length=200, null=True, blank=True)

    sixteen_s = JSONField(default=dict)  # {'16S NCBI-db': [{'description': 'E. coli', 'taxid': 123, 'evalue': 0.0}, ...], ...}

    BUSCO = JSONField(default=dict)  # {C:2,D:2,F:2,M:2,S:2,T:2]}
    BUSCO_percent_single = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    # format(self.BUSCO['S'] / self.BUSCO['T'], ".1%")

    # information about annotation
    custom_annotations = JSONField(default=list)  # [{"date": "2016-02-29", "file": "FAM19038.ko", "type": "KEGG"}]

    # accession numbers if the genome has been published
    bioproject_accession = models.CharField(max_length=20, null=True, blank=True)
    biosample_accession = models.CharField(max_length=20, null=True, blank=True)
    genome_accession = models.CharField(max_length=20, null=True, blank=True)

    # literature references
    literature_references = JSONField(default=list)  # ["ref1", "ref2",]

    def natural_key(self):
        return self.identifier

    @property
    def parent(self):
        return self.taxid

    def set_representative(self):
        self.strain.set_representative(self)

    @property
    def taxscientificname(self):
        return self.taxid.taxscientificname

    @property
    def member_html(self):
        tsi = self.taxid.taxscientificname
        return F'<div class="member ogb-tag" data-species="{tsi}" data-toggle="tooltip">{self.identifier}</div>'

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
        return self.representative is not None

    @property
    def restricted(self) -> bool:
        return self.strain.restricted

    @property
    def taxid(self) -> TaxID:
        return self.strain.taxid

    def base_path(self, relative=True) -> str:
        rel = F"strains/{self.strain.name}/members/{self.identifier}"
        if relative:
            return rel
        else:
            return F"{settings.GENOMIC_DATABASE}/{rel}"

    @property
    def rel_base_path(self):
        return self.base_path(relative=True)

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

    @property
    def all_tags(self):
        return (self.tags.all() | self.strain.tags.all()).distinct()

    def __str__(self):
        return self.identifier

    def invariant(self):
        msg = "Error in Member {}!".format(self.identifier)

        assert self.identifier.startswith(self.strain.name), msg

        # Check if mandatory files exist:
        for file in [self.cds_faa, self.cds_gbk, self.cds_gff, self.assembly_fasta]:
            assert os.path.isfile(file(relative=False)), "file does not exist: {}".format(file)

        # Check if non-mandatory files exist:
        for file in [self.cds_sqn, self.cds_ffn]:
            if file(relative=False):
                assert os.path.isfile(file(relative=False)), "file does not exist: {}".format(file)

        # check all JSONFields:
        if self.origin_included_sequences:
            for entry in self.origin_included_sequences:
                assert isinstance(entry['taxid'], int), msg
                assert isinstance(entry['percentage'], float), msg

        if self.origin_excluded_sequences:
            for entry in self.origin_excluded_sequences:
                assert isinstance(entry['taxid'], int), msg
                assert isinstance(entry['percentage'], float), msg

        if self.BUSCO:
            for char in ['C', 'D', 'F', 'M', 'S', 'T']:
                assert isinstance(self.BUSCO[char], int), msg

        if self.custom_annotations:
            for tool in self.custom_annotations:
                assert Member.is_valid_date(tool['date']), msg
                assert os.path.exists(F"{self.base_path(relative=False)}/{tool['file']}"), msg
                assert isinstance(tool['type'], str), msg

        for envs in [self.env_broad_scale, self.env_medium, self.env_local_scale]:
            if envs:
                assert self.is_valid_env(envs), msg

        # test sequencing info
        if self.sequencing_date:
            for date in self.sequencing_date.split("//"): assert self.is_valid_date(date)

        # test assembly tool
        if self.assembly_date:
            for date in self.assembly_date.split("//"): assert self.is_valid_date(date)

        # Test certain string fields
        if self.literature_references:
            for reference in self.literature_references:
                assert Member.is_valid_reference(reference), msg

        if self.geographical_coordinates:
            import re
            assert re.match("^([0-9]{1,2})(\.[0-9]{1,4})? (N|S) ([0-9]{1,2})(\.[0-9]{1,4})? (W|E)$",
                            self.geographical_coordinates), msg
        return True

    @property
    def get_tag_html(self) -> str:
        tags = (self.tags.all() | self.strain.tags.all()).distinct()
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

    def delete(self, *args, **kwargs):
        self.genome.wipe_data()
        self.genome.delete()
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
            print("Poorly formatted env: {}".format(env))
            return False
        return True

    @staticmethod
    def get_selector_to_description_dict():
        selector_to_description_dict = {
            'strain.name': {'filter_type': 'text', 'description': 'Strain'},
            'identifier': {'filter_type': 'text', 'description': 'Identifier'},
            'old_identifier': {'filter_type': 'text', 'description': 'Old Identifier'},
            'representative': {'filter_type': 'binary', 'description': 'Representative'},
            'strain.restricted': {'filter_type': 'binary', 'description': 'Restricted'},
            'contaminated': {'filter_type': 'binary', 'description': 'Contaminated'},
            'member_tags': {'filter_type': 'custom-tags', 'description': 'Member-Tags'},
            'strain_tags': {'filter_type': 'custom-tags', 'description': 'Strain-Tags'},
            'isolation_date': {'filter_type': 'range_date', 'description': 'Isolation date'},
            'env_broad_scale': {'filter_type': 'no-filter', 'description': 'Broad Isolation Environment'},
            'env_local_scale': {'filter_type': 'no-filter', 'description': 'Local Isolation Environment'},
            'env_medium': {'filter_type': 'no-filter', 'description': 'Environment Medium'},
            'growth_condition': {'filter_type': 'no-filter', 'description': 'Growth Condition'},
            'geographical_coordinates': {'filter_type': 'no-filter', 'description': 'Isolation Coordinates'},
            'geographical_name': {'filter_type': 'no-filter', 'description': 'Geographical Name'},
            'sequencing_tech': {'filter_type': 'multi_select', 'description': 'Sequencing Technology'},
            'sequencing_tech_version': {'filter_type': 'no-filter', 'description': 'Sequencing Technology Version'},
            'sequencing_date': {'filter_type': 'no-filter', 'description': 'Sequencing Date'},
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
            'BUSCO_percent_single': {'filter_type': 'no-filter', 'description': 'BUSCO [%S]'},
            'bioproject_accession': {'filter_type': 'no-filter', 'description': 'Bioproject'},
            'biosample_accession': {'filter_type': 'no-filter', 'description': 'Biosample'},
            'genome_accession': {'filter_type': 'no-filter', 'description': 'Genome Accession'},
            'literature_references': {'filter_type': 'no-filter', 'description': 'Literature References'},
            'strain.taxid.taxsuperkingdom': {'filter_type': 'multi_select', 'description': 'Superkingdom'},
            'strain.taxid.taxphylum': {'filter_type': 'multi_select', 'description': 'Phylum'},
            'strain.taxid.taxclass': {'filter_type': 'multi_select', 'description': 'Class'},
            'strain.taxid.taxorder': {'filter_type': 'multi_select', 'description': 'Order'},
            'strain.taxid.taxfamily': {'filter_type': 'multi_select', 'description': 'Family'},
            'strain.taxid.taxgenus': {'filter_type': 'multi_select', 'description': 'Genus'},
            'strain.taxid.taxspecies': {'filter_type': 'multi_select', 'description': 'Species'},
            'strain.taxid.taxsubspecies': {'filter_type': 'multi_select', 'description': 'Subspecies'},
            'strain.taxid.taxscientificname': {'filter_type': 'multi_select', 'description': 'Taxonomy'},
            'strain.taxid.id': {'filter_type': 'multi_select', 'description': 'TaxID'}
        }
        return selector_to_description_dict
