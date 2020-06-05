from django.contrib import admin
from .models import Strain, Genome, Tag

admin.site.register(Strain)
admin.site.register(Genome)
admin.site.register(Tag)