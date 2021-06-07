import os
from OpenGenomeBrowser import settings
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models.query import QuerySet
from website.models.helpers import KeyValueStore


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

    @property
    def html(self):
        return F'<span class="taxid ogb-tag" data-species="{self.taxscientificname}">{self.taxscientificname}</span>'

    def get_child_taxids(self) -> QuerySet:
        return TaxID.objects.get_queryset_descendants(TaxID.objects.filter(id=self.id), include_self=True)

    def get_child_organisms(self) -> QuerySet:
        from .Organism import Organism
        taxid_qs = self.get_child_taxids()
        return Organism.objects.filter(taxid__in=list(taxid_qs.values_list(flat=True)))

    def get_child_genomes(self, representative=None, contaminated=None, restricted=None) -> QuerySet:
        from .Genome import Genome
        qs = Genome.objects.filter(organism__in=self.get_child_organisms())

        if representative is not None:
            qs = qs.filter(representative__isnull=not representative)
        if contaminated is not None:
            qs = qs.filter(contaminated=contaminated)
        if restricted is not None:
            qs = qs.filter(organism__restricted=restricted)

        return qs.distinct()

    @staticmethod
    def get_or_create(taxid: int):
        try:
            return TaxID.objects.get(id=taxid)

        except TaxID.DoesNotExist:
            from lib.color_generator.ColorGenerator import ColorGenerator
            from lib.get_tax_info.get_tax_info import GetTaxInfo
            from lib.get_tax_info.get_tax_info import TaxID as RawTaxID
            RawTaxID.gti = GetTaxInfo()
            taxid_colors = TaxIdColors()

            if taxid == 1:  # create root node without parent
                t = RawTaxID(taxid=1)
                color_string = taxid_colors.get_or_generate_color(key=1)
                color_int = ColorGenerator.import_string(color_string)
                text_color_white = ColorGenerator.is_dark(color_int=color_int, is_float=False)
                root_node = TaxID(id=1,
                                  taxscientificname=t.scientific_name,
                                  rank=t.rank,
                                  color=color_string,
                                  text_color_white=text_color_white
                                  )
                root_node.save()
                return root_node

            else:  # create regular node
                t = RawTaxID(taxid=taxid)
                parent = TaxID.get_or_create(taxid=t.parent_taxid)
                color_string = taxid_colors.get_or_generate_color(key=taxid)
                color_int = ColorGenerator.import_string(color_string)
                text_color_white = ColorGenerator.is_dark(color_int=color_int, is_float=False)
                # create new NCBI_TaxID
                tid = TaxID(
                    id=taxid,
                    taxscientificname=t.scientific_name,

                    parent=parent,
                    rank=t.rank,
                    color=color_string,
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

        basepaths = [os.path.abspath(F'{settings.BASE_DIR}/website/static/global/css'),
                     os.path.abspath(F'{settings.BASE_DIR}/static_root/global/css')]

        span_css = ''
        svg_css = '[data-species-label] { stroke-width: 3px; paint-order: stroke; cursor: pointer; }\n'

        for taxid in all_taxids:
            span_css += F'[data-species="{taxid.taxscientificname}"] {{' + \
                       F'background-color: rgb({taxid.color}) !important; ' + \
                       F'color: {"white" if taxid.text_color_white else "black"} !important' + \
                       '}\n'
            svg_css += F'[data-species-label="{taxid.taxscientificname}"] {{' + \
                       F'stroke: rgb({taxid.color}); ' + \
                       F'fill: {"white" if taxid.text_color_white else "black"} !important' + \
                       '}\n'
            # F'text-shadow: 1px 0 3px rgb({taxid.color}), -1px 0 3px rgb({taxid.color}), 0 1px 3px rgb({taxid.color}), 0 -1px 3px rgb({taxid.color}); ' + \

        for basepath in basepaths:
            # ensure parent exists
            file = F'{basepath}/taxid_color.css'
            os.makedirs(os.path.dirname(file), exist_ok=True)
            open(file, 'w').write(span_css)

            # ensure parent exists
            file = F'{basepath}/taxid_color_label.css'
            os.makedirs(os.path.dirname(file), exist_ok=True)
            open(file, 'w').write(svg_css)


class TaxIdColors(KeyValueStore):
    _file = F'{settings.GENOMIC_DATABASE}/taxid_color_dict.json'
    _model = TaxID
    _key = 'id'
    _key_isint = True
    _value = 'color'

