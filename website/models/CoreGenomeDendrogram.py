import os.path

from django.db import models
from hashlib import sha224

from OpenGenomeBrowser.settings import ORTHOFINDER_ENABLED, CACHE_DIR, CACHE_MAXSIZE
from plugins import calculate_core_genome_dendrogram
from .GenomeContent import GenomeContent
from .Genome import Genome
from lib.ogb_cache.ogb_cache import clear_cache


class DendrogramManager(models.Manager):
    def get_or_create(self, genomes, **kwargs):
        assert ORTHOFINDER_ENABLED, 'OrthoFinder is disabled!'

        hash = Genome.hash_genomes(genomes)

        # return if exists
        try:
            return super(DendrogramManager, self).get(unique_id=hash), False
        except CoreGenomeDendrogram.DoesNotExist:
            pass

        # create placeholder-genome_similarity in database, start huey job
        new_dendrogram = CoreGenomeDendrogram(unique_id=hash, newick='', status='R')
        new_dendrogram.save()
        new_dendrogram.genomes.set(genomes)

        new_dendrogram.reload()

        return new_dendrogram, True

    def bulk_create(self, objs, *args, **kwargs):
        raise NotImplementedError('This operation is not currently supported.')


class CoreGenomeDendrogram(models.Model):
    """
    Dendrograms calculated using OrthoFinder.
        :param newick

    The ANI-relationship is symmetrical. Only one object is created for every combination:
        :param from_genome: smaller genome.identifier according to Python lexicographical ordering
        :param to_genome: larger genome.identifier according to Python lexicographical ordering
    """

    objects = DendrogramManager()

    unique_id = models.CharField(max_length=56, unique=True)  # sha224-encoded list of identifiers

    newick = models.TextField()

    genomes = models.ManyToManyField(GenomeContent)

    DONE = "D"
    RUNNING = "R"
    FAILED = "F"
    STATUS_CHOICES = ((DONE, 'DONE'), (RUNNING, 'RUNNING'), (FAILED, 'FAILED'))

    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    message = models.TextField(default='')

    def reload(self):
        self.newick = ''
        self.status = 'R'
        self.message = ''
        self.save()
        calculate_core_genome_dendrogram(genomes=self.genomes.all(), cache_file=self.cache_file_path(relative=False))

    def cache_file_path(self, relative=True) -> str:
        relative_path = f'core-genome-dendrogram/{self.unique_id}.tar.gz'
        return relative_path if relative else f'{CACHE_DIR}/{relative_path}'

    @property
    def has_cache_file(self) -> bool:
        return os.path.isfile(self.cache_file_path(relative=False))

    @staticmethod
    def clean_cache():
        clear_cache(cache_fn_dir=f'{CACHE_DIR}/core-genome-dendrogram', maxsize=CACHE_MAXSIZE)
