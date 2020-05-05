from django.contrib import admin
from .models import Strain, Member, Tag

admin.site.register(Strain)
admin.site.register(Member)
admin.site.register(Tag)