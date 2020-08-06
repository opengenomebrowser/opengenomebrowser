from django.db import models
from .TaxID import TaxID
from .Tag import Tag
from OpenGenomeBrowser import settings


# class StrainManager(models.Manager):
#     def taxid(self):
#         return self.filter()

class Strain(models.Model):
    """
    Represents a biologically distinct entity.

    Imported from the contents of database/genomes/*
    """

    name = models.SlugField(max_length=40, unique=True)
    alternative_name = models.CharField(max_length=200, null=True, blank=True)
    taxid = models.ForeignKey(TaxID, on_delete=models.CASCADE)  # if unknown: 32644; mixture: 1427524
    restricted = models.BooleanField(default=False)

    tags = models.ManyToManyField(Tag)

    @property
    def parent(self):
        return self.taxid

    @property
    def taxscientificname(self):
        return self.taxid.taxscientificname

    def natural_key(self):
        return self.name

    @property
    def html(self):
        return F'<div class="strain ogb-tag" data-species="{self.taxid.taxscientificname}" data-toggle="tooltip">{self.name}</div>'

    @property
    def get_tag_html(self) -> str:
        html = [tag.get_html_badge() for tag in self.tags.all().order_by('tag')]
        return " ".join(html)

    def get_taxonomy(self, rank: str = None) -> str:
        return self.taxid.get_taxonomy(rank)

    def set_representative(self, genome):
        from .Genome import Genome
        assert genome == None or isinstance(genome, Genome)

        if hasattr(self, 'representative'):
            current_representative = self.representative
            current_representative.representative = None
            current_representative.save()

        if genome:
            genome.representative = self
            genome.save()

    @property
    def metadata_json(self):
        return F'{settings.GENOMIC_DATABASE}/strains/{self.name}/strain.json'

    def __str__(self):
        return self.name

    def invariant(self):
        # sanity check
        assert self.genome_set.count() > 0, "Error in strain {}: Has no genome!".format(self.name)
        assert hasattr(self, 'representative'), "Error in strain {}: Has no representative!".format(self.name)

        # ensure metadata matches genome
        import json
        from website.models.StrainSerializer import StrainSerializer
        from dictdiffer import diff
        ss = StrainSerializer()
        im_dict = json.loads(open(F'{settings.GENOMIC_DATABASE}/strains/{self.name}/strain.json').read())
        im_dict = ss._convert_natural_keys_to_pks(im_dict)
        exp_dict = ss.export_strain(self.name)
        assert im_dict == exp_dict, F'\n{im_dict}\n{exp_dict}\n{list(diff(im_dict, exp_dict))}'

        return True
