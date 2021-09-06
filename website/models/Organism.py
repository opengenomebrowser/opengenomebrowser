from django.db import models
from .TaxID import TaxID
from .Tag import Tag
from OpenGenomeBrowser import settings
from website.models.helpers.backup_file import read_file_or_default, overwrite_with_backup


class Organism(models.Model):
    """
    Represents a biologically distinct entity.

    Imported from the contents of database/genomes/*
    """

    name = models.CharField(max_length=40, unique=True)
    alternative_name = models.CharField(max_length=200, null=True, blank=True)
    taxid = models.ForeignKey(TaxID, on_delete=models.CASCADE)  # if unknown: 32644; mixture: 1427524
    restricted = models.BooleanField(default=False)

    representative = models.OneToOneField('website.Genome', related_name="representative",
                                          on_delete=models.RESTRICT, blank=True, null=True)

    tags = models.ManyToManyField(Tag, blank=True)

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
        classes = ['organism', 'ogb-tag']
        if self.restricted:
            classes.append('restricted')
        return f'<span class="{" ".join(classes)}" data-species="{self.taxid.taxscientificname}">{self.name}</span>'

    @property
    def get_tag_html(self) -> str:
        html = [tag.get_html_badge() for tag in self.tags.all().order_by('tag')]
        return " ".join(html)

    def get_taxonomy(self, rank: str = None) -> str:
        return self.taxid.get_taxonomy(rank)

    def set_representative(self, genome):
        self.representative = genome
        self.save()

    def base_path(self, relative=True) -> str:
        rel = F"organisms/{self.name}"
        return rel if relative else f'{settings.GENOMIC_DATABASE}/{rel}'

    @property
    def metadata_json(self):
        return f'{settings.GENOMIC_DATABASE}/organisms/{self.name}/organism.json'

    def markdown_path(self, relative=True) -> str:
        return F"{self.base_path(relative)}/organism.md"

    def markdown(self, default=None) -> str:
        return read_file_or_default(file=self.markdown_path(relative=False), default=default, default_if_empty=True)

    def set_markdown(self, md: str, user: str = None):
        overwrite_with_backup(file=self.markdown_path(relative=False), content=md, user=user, delete_if_empty=True)

    def __str__(self):
        return self.name

    def invariant(self):
        # sanity check
        assert self.genome_set.count() > 0, "Error in organism {}: Has no genome!".format(self.name)
        assert hasattr(self, 'representative'), "Error in organism {}: Has no representative!".format(self.name)

        # ensure metadata matches organism
        import json
        from website.serializers import OrganismSerializer
        im_dict = json.loads(open(f'{settings.GENOMIC_DATABASE}/organisms/{self.name}/organism.json').read())
        matches, differences = OrganismSerializer.json_matches_organism(organism=self, json_dict=im_dict)
        assert matches, f'json and database do not match. organism: {self.name} differences: {differences}'

        return True
