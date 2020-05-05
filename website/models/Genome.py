import os
from django.db import models
from django.contrib.postgres.fields import JSONField
from website.models.Annotation import Annotation, AnnotationRegex
from .TaxID import TaxID
from .ANI import ANI


class Genome(models.Model):
    """
    Represents a Member's genome.

    Imported from database/genomes/strain/members/{1_assemblies,2_annotations}
    """
    identifier = models.CharField('unique identifier', max_length=50, unique=True, primary_key=True)

    gbk_file_size = models.IntegerField()
    custom_files = JSONField(default=list)  # list [{"date": "2016-02-29", "file": "FAM19038.ko", "type": "KEGG"}]

    annotations = models.ManyToManyField(Annotation)

    ani_similarity = models.ManyToManyField('self', through=ANI, symmetrical=True, related_name='ani_similarity+')

    @property
    def parent(self):
        return self.taxid

    @property
    def taxid(self) -> TaxID:
        return self.member.taxid

    @property
    def taxscientificname(self):
        return self.taxid.taxscientificname

    def __str__(self):
        return self.identifier

    def natural_key(self):
        return self.identifier

    @property
    def strain(self):
        return self.member.strain

    def get_ani_similarity(self, partner_genome) -> ANI:
        return ANI.objects.get_or_create(self, partner_genome)

    def get_ani_partners(self) -> models.QuerySet:
        to_partners = Genome.objects.filter(from_ani__in=self.to_ani.all())
        from_partners = Genome.objects.filter(to_ani__in=self.from_ani.all())
        return to_partners.union(from_partners)

    def update(self):
        # was the gbk file changed? if so -> reload everything
        if self.gbk_file_size != os.stat(self.member.cds_gbk).st_size:
            self.load_genome()
            self.save()
            return

        # was one of the files removed or changed? if so -> reload everything
        for file_dict in self.custom_files:
            if file_dict not in self.member.custom_annotations:
                self.load_genome()
                self.save()
                return

        # was a new file added? -> load it
        for file_dict in self.member.custom_annotations:
            if file_dict not in self.custom_files:
                self.load_custom_file(file_dict)
        self.save()

    def wipe_data(self):
        self.custom_files = []
        self.annotations.all().delete()

    def load_genome(self):
        from .Gene import Gene
        from Bio import SeqIO, SeqRecord
        import re
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

        with open(self.member.cds_gbk, "r") as input_handle:
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
        Gene.objects.bulk_create([Gene(identifier=identifier, genome=self) for identifier in gene_id_set])

        # Create Annotation-Objects
        self.add_many_annotations(self=self, anno_type='GC', annos_to_add=gene_code_set)
        self.add_many_annotations(self=self, anno_type='GP', annos_to_add=product_set)
        self.add_many_annotations(self=self, anno_type='EC', annos_to_add=ec_set)

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
        self.gbk_file_size = os.stat(self.member.cds_gbk).st_size

        # load custom files:
        for file_dict in self.member.custom_annotations:
            if file_dict not in self.custom_files:
                self.load_custom_file(file_dict)

    def load_custom_file(self, file_dict):
        from .Gene import Gene
        print("       add new file:", file_dict)

        if file_dict['type'] == 'KEGG':
            anno_type = AnnotationRegex.KEGGGENE
        elif file_dict['type'] == 'GO':
            anno_type = AnnotationRegex.GENEONTOLOGY
        elif file_dict['type'] == 'R':
            anno_type = AnnotationRegex.KEGGREACTION
        elif file_dict['type'] == 'EC':
            anno_type = AnnotationRegex.ENZYMECOMMISSION
        elif file_dict['type'] == 'custom':
            anno_type = AnnotationRegex.CUSTOM
        else:
            print("Custom file is poorly formatted: ", file_dict)
            print("Only the following types are allowed: KEGG, GO, EC, custom")
            raise NotImplementedError

        all_annotations = set()
        annotations_relationships = set()  # [('gene1', 'anno1), ('gene1', 'anno2), ...]

        with open(self.member.base_path + "3_annotations/" + file_dict['file']) as f:
            line = f.readline().strip()
            while line:
                line = line.split("\t")
                if len(line) == 2:
                    annotations = set(line[1].split(","))
                    for annotation in annotations:
                        assert anno_type.match_regex.match(
                            annotation) is not None, F"Error: Annotation '{annotation}' does not match regex '{anno_type.match_regex.pattern}'!"
                    all_annotations.update(annotations)
                    annotations_relationships.update([(line[0], anno) for anno in annotations])

                line = f.readline().strip()

        # Create Annotation-Objects and many-to-many relationships
        self.add_many_annotations(self=self, anno_type=anno_type.value, annos_to_add=all_annotations)
        objects = [Gene.annotations.through(gene_id=gene, annotation_id=anno) for gene, anno in
                   annotations_relationships]
        Gene.annotations.through.objects.bulk_create(objects, ignore_conflicts=True)

        self.custom_files.append(file_dict)

    @staticmethod
    def add_many_annotations(self, anno_type: str, annos_to_add: set):
        # static method because it's also used in KeggMap
        assert anno_type in Annotation.AnnotationTypes.values

        # create missing annotation objects
        db_has = set(Annotation.objects.all().values_list('name', flat=True))
        db_lacks = annos_to_add - db_has
        if len(db_lacks) > 0:
            Annotation.objects.bulk_create([Annotation(name=name, anno_type=anno_type) for name in db_lacks])

        # add new annotations to existing annotations
        map_has = set(self.annotations.all().values_list('name', flat=True))
        map_should_have = map_has.union(annos_to_add)
        self.annotations.set(Annotation.objects.filter(name__in=map_should_have))
