from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from website.admin.OgbAdminSite import OgbAdminSite
from website.admin.OrganismAdmin import OrganismAdmin, Organism
from website.admin.GenomeAdmin import GenomeAdmin, Genome
from website.admin.TagAdmin import TagAdmin, Tag
from website.admin.TaxIdAdmin import TaxIdAdmin, TaxID

ogb_admin_site = OgbAdminSite()

ogb_admin_site.register(User, UserAdmin)
ogb_admin_site.register(Group, GroupAdmin)
ogb_admin_site.register(Tag, TagAdmin)
ogb_admin_site.register(TaxID, TaxIdAdmin)
ogb_admin_site.register(Organism, OrganismAdmin)
ogb_admin_site.register(Genome, GenomeAdmin)
