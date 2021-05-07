from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from website.admin.OgbAdminSite import OgbAdminSite
from website.models import Organism, Genome, Tag
from website.admin.OrganismAdmin import OrganismAdmin
from website.admin.GenomeAdmin import GenomeAdmin
from website.admin.TagAdmin import TagAdmin

ogb_admin_site = OgbAdminSite()

ogb_admin_site.register(User, UserAdmin)
ogb_admin_site.register(Group, GroupAdmin)
ogb_admin_site.register(Tag, TagAdmin)
ogb_admin_site.register(Organism, OrganismAdmin)
ogb_admin_site.register(Genome, GenomeAdmin)
