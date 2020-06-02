import os
from OpenGenomeBrowser import settings
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models.query import QuerySet


class TaxID(MPTTModel):
    """
    Represents TaxID

    :param taxid:
    :param parent: TaxID object
    """

    id = models.IntegerField(primary_key=True)
    taxscientificname = models.CharField(max_length=110)

    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, related_name='children')
    rank = models.CharField(max_length=50)
    color = models.CharField(max_length=11)
    text_color_white = models.BooleanField()  # True == white, False == black

    taxsuperkingdom = models.CharField(max_length=110, null=True)
    taxphylum = models.CharField(max_length=110, null=True)
    taxclass = models.CharField(max_length=110, null=True)
    taxorder = models.CharField(max_length=110, null=True)
    taxfamily = models.CharField(max_length=110, null=True)
    taxgenus = models.CharField(max_length=110, null=True)
    taxspecies = models.CharField(max_length=110, null=True)
    taxsubspecies = models.CharField(max_length=110, null=True)

    class MPTTMeta:
        order_insertion_by = ['taxscientificname']

    def natural_key(self):
        return self.id

    def __str__(self):
        return self.taxscientificname

    @property
    def html_style(self):
        text_color = 'white' if self.text_color_white else 'black'
        return F'background-color:rgb({self.color});color:{text_color}'

    def get_child_taxids(self) -> QuerySet:
        return TaxID.objects.get_queryset_descendants(TaxID.objects.filter(id=self.id), include_self=True)

    def get_child_strains(self) -> QuerySet:
        taxid_qs = self.get_child_taxids()
        from .Strain import Strain
        return Strain.objects.filter(taxid__in=list(taxid_qs.values_list(flat=True)))

    def get_child_members(self, representatives_only=True) -> QuerySet:
        from .Member import Member
        strain_qs = self.get_child_strains()
        if representatives_only:
            return strain_qs.select_related('representative')  # Faster!
        else:
            return Member.objects.filter(strain__in=list(strain_qs.values_list(flat=True)))

    @staticmethod
    def get_or_create(taxid: int):
        try:
            return TaxID.objects.get(id=taxid)

        except TaxID.DoesNotExist:
            from lib.get_tax_info.get_tax_info import TaxID as RawTaxID
            from lib.tax_id_to_color.glasbey_wrapper import GlasbeyWrapper

            if taxid == 1:  # create root node without parent
                t = RawTaxID(taxid=1)
                color, text_color_white = GlasbeyWrapper.get_color_from_taxid(t.taxid, t.scientific_name)
                root_node = TaxID(id=1,
                                  taxscientificname=t.scientific_name,

                                  rank=t.rank,
                                  color=color,
                                  text_color_white=text_color_white
                                  )
                root_node.save()
                return root_node

            else:  # create regular node
                t = RawTaxID(taxid=taxid)
                parent = TaxID.get_or_create(taxid=t.parent_taxid)
                color, text_color_white = GlasbeyWrapper.get_color_from_taxid(taxid, t.scientific_name)
                # create new NCBI_TaxID
                tid = TaxID(
                    id=taxid,
                    taxscientificname=t.scientific_name,

                    parent=parent,
                    rank=t.rank,
                    color=color,
                    text_color_white=text_color_white,

                    # inherit from parent:
                    taxsuperkingdom=parent.taxsuperkingdom,
                    taxphylum=parent.taxphylum,
                    taxclass=parent.taxclass,
                    taxorder=parent.taxorder,
                    taxfamily=parent.taxfamily,
                    taxgenus=parent.taxgenus,
                    taxspecies=parent.taxspecies,
                    taxsubspecies=parent.taxsubspecies
                )

                tid.set_rank(t.rank, t.scientific_name)

                tid.save()
                return tid

    def set_rank(self, rank: str, name: str):
        setattr(self, "tax" + rank, name)

    def save(self, *args, **kwargs):
        # overwrite save to also check invariant
        assert self.invariant(), "Error in TaxID {}: invariant failed.".format(self.id)
        super(TaxID, self).save(*args, **kwargs)

    def invariant(self):
        if not self.parent:
            assert self.id == 1, "Error in TaxID {}: only root-node (TaxID=1) has no parent.".format(self.id)
            return True

        # color string must be of this format: '255,255,255'
        from re import match
        assert match(pattern='^[0-9]{1,3},[0-9]{1,3},[0-9]{1,3}$', string=self.color), \
            "Error in TaxID {}: RGB-values are poorly formatted: {}.".format(self.id, self.color)

        assert [0 >= int(c) >= 255 for c in self.color.split(",")], \
            "Error in TaxID {}: RGB-values must be between 0 and 255: {}.".format(self.id, self.color)

        # regular nodes must be related to root-node
        counter = 0
        ancestor_explorer = self
        while ancestor_explorer.parent and counter < 30:  # don't check more than 20 iterations
            ancestor_explorer = ancestor_explorer.parent
            counter += 1
        assert ancestor_explorer.id == 1, "Error in TaxID {}: Does not relate to root TaxID (1)!".format(self.id)
        return True

    def get_taxonomy(self, rank: str = None) -> str:
        if not rank:
            return self.taxscientificname
        return getattr(self, rank)

    @staticmethod
    def create_taxid_color_css():
        all_taxids = TaxID.objects.all()
        basepath = os.path.abspath(F'{settings.BASE_DIR}/website/static/global/css')
        div_css = open(F'{basepath}/taxid_color.css', 'w')
        label_css = open(F'{basepath}/taxid_color_label.css', 'w')
        for taxid in all_taxids:
            div_css.write(F'[data-species="{taxid.taxscientificname}"] {{' +
                          F'background-color: rgb({taxid.color}) !important; ' +
                          F'color: {"white" if taxid.text_color_white else "black"} !important' +
                          '}\n')
            label_css.write(F'[data-species-label="{taxid.taxscientificname}"] {{' +
                            F'text-shadow: 1px 0 3px rgb({taxid.color}), -1px 0 3px rgb({taxid.color}), 0 1px 3px rgb({taxid.color}), 0 -1px 3px rgb({taxid.color}); '
                            F'fill: {"white" if taxid.text_color_white else "black"} !important' +
                            '}\n')
