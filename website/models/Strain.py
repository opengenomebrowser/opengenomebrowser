from django.db import models
from django.db.utils import IntegrityError
import os
from .TaxID import TaxID
from .Tag import Tag


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

    def set_representative(self, member):
        from .Member import Member
        assert member == None or isinstance(member, Member)

        if hasattr(self, 'representative'):
            current_representative = self.representative
            current_representative.representative = None
            current_representative.save()

        if member:
            member.representative = self
            member.save()

    def __str__(self):
        return self.name

    def invariant(self):
        assert self.member_set.count() > 0, "Error in strain {}: Has no member!".format(self.name)
        assert hasattr(self, 'representative'), "Error in strain {}: Has no representative!".format(self.name)
        return True
