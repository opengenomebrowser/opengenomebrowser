#! /usr/bin/python3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import django environment to manipulate the Organism and Genome classes
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OpenGenomeBrowser.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from website.models import GenomeSimilarity, CoreGenomeDendrogram

failed_anis = GenomeSimilarity.objects.filter(status='F')
print('deleting failed anis:', failed_anis)
failed_anis.delete()

failed_dendros = CoreGenomeDendrogram.objects.filter(status='F')
print('deleting failed dendros:', failed_dendros)
failed_dendros.delete()

running_anis = GenomeSimilarity.objects.filter(status='R')
print('deleting running anis:', running_anis)
running_anis.delete()

running_dendros = CoreGenomeDendrogram.objects.filter(status='R')
print('deleting running dendros:', running_dendros)
running_dendros.delete()
