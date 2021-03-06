import os
from django.db import models
from django.db.models import JSONField
from website.models.Annotation import Annotation, AnnotationDescriptionFile, AnnotationType, annotation_types
from .TaxID import TaxID
from .GenomeSimilarity import GenomeSimilarity
from OpenGenomeBrowser import settings


class GenomeContent(models.Model):
    """
    Represents a genomes content.

    Imported from database/genomes/organisms/genomes/{1_assemblies,2_annotations}
    """
    identifier = models.CharField('unique identifier', max_length=50, unique=True, primary_key=True)

    n_genes = models.IntegerField('Number of genes', default=0)

    _gbk_file_size = models.IntegerField(default=0)

    custom_files = JSONField(default=list)  # list [{"date": "2016-02-29", "file": "FAM19038.ko", "type": "KEGG"}]

    annotations = models.ManyToManyField(Annotation)

    ani_similarity = models.ManyToManyField('self', through=GenomeSimilarity, symmetrical=True, related_name='ani_similarity+')

    @property
    def parent(self):
        return self.taxid

    @property
    def taxid(self) -> TaxID:
        return self.genome.taxid

    @property
    def taxscientificname(self):
        return self.taxid.taxscientificname

    def blast_dbs_path(self, relative=True):
        return F'{self.genome.base_path(relative=relative)}/.blast_dbs'

    def blast_db_fna(self, relative=True):
        return F'{self.blast_dbs_path(relative=relative)}/fna/{self.identifier}.fna'

    def blast_db_faa(self, relative=True):
        return F'{self.blast_dbs_path(relative=relative)}/faa/{self.identifier}.faa'

    def blast_db_ffn(self, relative=True):
        return F'{self.blast_dbs_path(relative=relative)}/ffn/{self.identifier}.ffn'

    def __str__(self):
        return self.identifier

    def natural_key(self):
        return self.identifier

    @property
    def html(self):
        return F'<div class="genome ogb-tag" data-species="{self.genome.taxid.taxscientificname}">{self.identifier}</div>'

    @property
    def organism(self):
        return self.genome.organism

    def get_ani_similarity(self, partner_genome) -> GenomeSimilarity:
        return GenomeSimilarity.objects.get_or_create(self, partner_genome)

    def get_ani_partners(self) -> models.QuerySet:
        to_partners = GenomeContent.objects.filter(from_ani__in=self.to_ani.all())
        from_partners = GenomeContent.objects.filter(to_ani__in=self.from_ani.all())
        return to_partners.union(from_partners)

    def update(self):
        # was the gbk file changed? if so -> reload everything
        if self._gbk_file_size != os.stat(self.genome.cds_gbk(relative=False)).st_size:
            self.load_genome()
            self.create_blast_dbs(reload=True)
            self.save()
            return

        # was one of the files removed or changed? if so -> reload everything
        for file_dict in self.custom_files:
            if file_dict not in self.genome.custom_annotations:
                self.wipe_data(genes=True)
                self.load_genome()
                self.save()
                return

        # was a new file added? -> load it
        for file_dict in self.genome.custom_annotations:
            if file_dict not in self.custom_files:
                self.load_custom_file(file_dict)
        self.save()

    def wipe_data(self, genes=False):
        if genes:
            self._gbk_file_size = 0
            self.gene_set.all().delete()
        self.custom_files = []
        self.annotations.clear()

    def load_genome(self):
        from .Gene import Gene
        from Bio import SeqIO
        print("       (re)loading gbk")
        self.wipe_data()

        # create objects in bulk -> much faster
        gene_id_set = set()
        gene_code_set = set()
        product_set = set()
        ec_set = set()
        gene_code_relationships = set()  # [('gene1', 'anno1), ('gene1', 'anno2), ...]
        product_relationships = set()
        ec_relationships = set()

        # regex_split_gene_code = re.compile('^(.+)(_[0-9]+)$')
        # disallowed_types = ['CDS', 'misc_RNA', 'rRNA', 'repeat_region', 'tRNA', 'tmRNA']

        with open(self.genome.cds_gbk(relative=False), "r") as input_handle:
            for scf in SeqIO.parse(input_handle, "genbank"):
                for f in scf.features:
                    if 'locus_tag' in f.qualifiers:
                        # if f.type not in disallowed_types and 'locus_tag' in f.qualifiers:
                        assert len(f.qualifiers["locus_tag"]) == 1
                        locus_tag = f.qualifiers["locus_tag"][0]
                        gene_id_set.add(locus_tag)
                        if 'pseudo' in f.qualifiers:
                            gene_code_set.add('pseudo-gene')
                            gene_code_relationships.add((locus_tag, 'pseudo-gene'))
                        else:
                            if 'gene' in f.qualifiers:
                                # gene_code = regex_split_gene_code.match(f.qualifiers['gene'])
                                # if gene_code:
                                #     d['gene'] = gene_code.groups()[0]
                                for ge in f.qualifiers['gene']:
                                    gene_code_set.add(ge)
                                    gene_code_relationships.add((locus_tag, ge))
                            if 'product' in f.qualifiers:
                                for pr in f.qualifiers['product']:
                                    pr = pr.replace(',', '-').replace(';', '-')
                                    product_set.add(pr)
                                    product_relationships.add((locus_tag, pr))
                            if 'EC_number' in f.qualifiers:
                                for ec in f.qualifiers['EC_number']:
                                    ec_set.add('EC:' + ec)
                                    ec_relationships.add((locus_tag, 'EC:' + ec))

        # create Gene objects
        Gene.objects.bulk_create([Gene(identifier=identifier, genomecontent=self) for identifier in gene_id_set])

        # Create Annotation-Objects
        self.add_many_annotations(model=self, anno_type='GC', annos_to_add=gene_code_set)
        self.add_many_annotations(model=self, anno_type='GP', annos_to_add=product_set)
        self.add_many_annotations(model=self, anno_type='EC', annos_to_add=ec_set)

        # Create many-to-many relationships
        # Gene-Codes
        objects = [Gene.annotations.through(gene_id=gene, annotation_id=anno) for gene, anno in
                   gene_code_relationships]
        Gene.annotations.through.objects.bulk_create(objects)
        # Product
        objects = [Gene.annotations.through(gene_id=gene, annotation_id=anno) for gene, anno in
                   product_relationships]
        Gene.annotations.through.objects.bulk_create(objects)
        # EC
        objects = [Gene.annotations.through(gene_id=gene, annotation_id=anno) for gene, anno in ec_relationships]
        Gene.annotations.through.objects.bulk_create(objects)

        # Save file size of imported gbk.
        self.n_genes = len(gene_id_set)
        self._gbk_file_size = os.stat(self.genome.cds_gbk(relative=False)).st_size

        # load custom files:
        for file_dict in self.genome.custom_annotations:
            if file_dict not in self.custom_files:
                self.load_custom_file(file_dict)

    def create_blast_dbs(self, reload=False):
        # do nothing if the .blast_dbs-folder exists
        if os.path.isdir(self.blast_dbs_path(relative=False)):
            if reload:
                import shutil
                shutil.rmtree(self.blast_dbs_path(relative=False))
            else:
                return

        blastable_files = [
            (self.genome.assembly_fasta(relative=False), self.blast_db_fna(relative=False), 'nucl'),
            (self.genome.cds_faa(relative=False), self.blast_db_faa(relative=False), 'prot'),
            (self.genome.cds_ffn(relative=False), self.blast_db_ffn(relative=False), 'nucl')
        ]

        from lib.ncbiblast.ncbi_blast.blast_wrapper import Blast
        blast = Blast(system_blast=True)

        for fasta, blast_db_location, dbtype in blastable_files:
            if not os.path.isdir(blast_db_location):
                os.makedirs(os.path.dirname(blast_db_location))
                os.symlink(src=fasta, dst=blast_db_location)
            blast.mkblastdb(file=blast_db_location, dbtype=dbtype, overwrite=True)

    def load_custom_file(self, file_dict):
        print("       add new file:", file_dict)
        if file_dict['type'] == 'eggnog':
            self.load_eggnog_file(file_dict)
        else:
            self.load_regular_file(file_dict)

        self.custom_files.append(file_dict)

    def load_eggnog_file(self, file_dict):
        assert file_dict['type'] == 'eggnog'
        from .Gene import Gene

        go = (set(), set(), annotation_types['GO'])  # gene ontology
        ec = (set(), set(), annotation_types['EC'])  # enzyme commission
        kg = (set(), set(), annotation_types['KG'])  # kegg gene
        kr = (set(), set(), annotation_types['KR'])  # kegg reaction
        ep = (set(), set(), annotation_types['EP'])  # eggnog protein name
        eo = (set(), set(), annotation_types['EO'])  # eggnog ortholog
        ed = (set(), set(), annotation_types['ED'])  # eggnog description

        def add_anno(annotations: list, all_annotations, annotations_relationships, anno_type: AnnotationType):
            for annotation in annotations:
                assert anno_type.regex.match(
                    annotation) is not None, F"Error: Annotation '{annotation}' does not match regex '{anno_type.regex.pattern}'!"
                all_annotations.update(annotations)
                annotations_relationships.update([(locus_tag, anno) for anno in annotations])
            pass

        with open(F"{self.genome.base_path(relative=False)}/{file_dict['file']}") as f:
            # skip header
            head = [next(f).rstrip() for x in range(4)]
            for h in head:
                assert h.startswith('#'), F'Error parsing file: {file_dict}'

            # parse file
            line = f.readline()[:-1]
            while line:
                line = line.split("\t")
                if len(line) != 22:
                    break

                locus_tag = line[0].rsplit('|', maxsplit=1)[-1]

                if line[6] != "":
                    add_anno(line[6].split(','), *go)
                if line[7] != "":
                    add_anno([f'EC:{l}' for l in line[7].split(',')], *ec)
                if line[8] != "":
                    add_anno([l[3:] for l in line[8].split(',')], *kg)
                if line[11] != "":
                    add_anno(line[11].split(','), *kr)
                if line[5] != "":
                    add_anno([f'EP:{line[5]}'], *ep)
                if line[18] != "":
                    add_anno([f'EO:{line[18].split("@", maxsplit=1)[0]}'], *eo)
                if line[21] != "":
                    add_anno([f"ED:{line[21].split(',', maxsplit=1)[0].split(';', maxsplit=1)[0]}"], *ed)

                line = f.readline()[:-1]

            # parse end of file
            for line in f.readlines():
                assert line.startswith('#'), F'Error parsing file: {file_dict}'

        # Create Annotation-Objects and many-to-many relationships
        for all_annotations, annotations_relationships, anno_type in (go, ec, kg, kr, ep, eo, ed):
            self.add_many_annotations(model=self, anno_type=anno_type.anno_type, annos_to_add=all_annotations)
            objects = [Gene.annotations.through(gene_id=gene, annotation_id=anno) for gene, anno in
                       annotations_relationships]
            Gene.annotations.through.objects.bulk_create(objects, ignore_conflicts=True)

    def load_regular_file(self, file_dict):
        from .Gene import Gene

        anno_type = file_dict['type']
        assert anno_type in annotation_types, \
            f'Error in annotation file:{file_dict}\nType {anno_type} is not defined in {settings.GENOMIC_DATABASE}/annotations.json.'
        regex = annotation_types[anno_type].regex

        all_annotations = set()  # {'anno1', 'anno2', ...}
        annotations_relationships = set()  # {('gene1', 'anno1), ('gene1', 'anno2'), ...}

        with open(F"{self.genome.base_path(relative=False)}/{file_dict['file']}") as f:
            line = f.readline().strip()
            while line:
                line = line.split("\t")
                if len(line) == 2:
                    annotations = set(a.strip() for a in line[1].split(","))
                    for annotation in annotations:
                        assert regex.match(
                            annotation) is not None, F"Error: Annotation '{annotation}' does not match regex '{regex.pattern}'!"
                    all_annotations.update(annotations)
                    annotations_relationships.update([(line[0], anno) for anno in annotations])

                line = f.readline().strip()

        # Create Annotation-Objects and many-to-many relationships
        self.add_many_annotations(model=self, anno_type=anno_type, annos_to_add=all_annotations)
        objects = [Gene.annotations.through(gene_id=gene, annotation_id=anno) for gene, anno in
                   annotations_relationships]
        Gene.annotations.through.objects.bulk_create(objects, ignore_conflicts=True)

    @staticmethod
    def add_many_annotations(model, anno_type: str, annos_to_add: set):
        # static method because it's also used elsewhere
        assert anno_type in annotation_types

        # create missing annotation objects (without description)
        Annotation.objects.bulk_create([
            Annotation(name=name, anno_type=anno_type)
            for name in annos_to_add], ignore_conflicts=True)

        # add new annotations to existing annotations
        map_has = set(model.annotations.all().values_list('name', flat=True))
        map_should_have = map_has.union(annos_to_add)
        model.annotations.set(Annotation.objects.filter(name__in=map_should_have))

        # update descriptions where missing
        try:
            adf = AnnotationDescriptionFile(anno_type=anno_type, create_cdb=False)
            adf.update_descriptions(reload=False)
        except FileNotFoundError:
            pass
