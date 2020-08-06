from django.db import models
import hashlib
from website.tasks import calculate_orthofinder
from .GenomeContent import GenomeContent



class DendrogramManager(models.Manager):
    def get_or_create(self, genomes, **kwargs):
        hash = CoreGenomeDendrogram.hash_genomes(genomes)

        # return if exists
        try:
            return super(DendrogramManager, self).get(unique_id=hash), False
        except CoreGenomeDendrogram.DoesNotExist:
            pass

        # create placeholder-genome_similarity in database, start huey job
        new_dendrogram = CoreGenomeDendrogram(unique_id=hash, newick='', status='R')
        new_dendrogram.save()

        new_dendrogram.genomes.set(genomes)


        print('calculate!')
        calculate_orthofinder(genomes=genomes)

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

    newick = models.TextField()  # TextFields have an unlimited number of characters

    genomes = models.ManyToManyField(GenomeContent)

    DONE = "D"
    RUNNING = "R"
    FAILED = "F"
    STATUS_CHOICES = ((DONE, 'DONE'), (RUNNING, 'RUNNING'), (FAILED, 'FAILED'))

    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    @staticmethod
    def hash_genomes(genomes) -> str:
        identifiers = sorted(set(g.identifier for g in genomes))
        identifier_string = ' '.join(identifiers)
        hash = hashlib.sha224(identifier_string.encode('utf-8')).hexdigest()
        assert len(hash) == 56
        return hash
