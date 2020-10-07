from django.db import models
from plugins import calculate_genome_similarity


def _sort(genome1, genome2):
    # return alphabetically "smaller" genome first
    if genome1.identifier < genome2.identifier:
        return genome1, genome2
    else:
        return genome2, genome1


class GenomeSimilarityQuerySet(models.query.QuerySet):
    def get(self, from_genome, to_genome, **kwargs):
        from_genome, to_genome = _sort(from_genome, to_genome)
        return super(GenomeSimilarityQuerySet, self).get(from_genome=from_genome, to_genome=to_genome, **kwargs)


class GenomeSimilarityManager(models.Manager.from_queryset(GenomeSimilarityQuerySet)):
    def get_or_create(self, from_genome, to_genome, **kwargs):
        from_genome, to_genome = _sort(from_genome, to_genome)

        # return if exists
        try:
            return super(GenomeSimilarityManager, self).get(from_genome=from_genome, to_genome=to_genome, **kwargs), False
        except GenomeSimilarity.DoesNotExist:
            pass

        # create if similarity was specified
        if 'similarity' in kwargs:
            return super(GenomeSimilarityManager, self).get_or_create(from_genome=from_genome, to_genome=to_genome, similarity=1,
                                                                      status='D')

        if from_genome == to_genome:
            # similarity must be 1
            new_sim = GenomeSimilarity(from_genome=from_genome, to_genome=to_genome, similarity=1, status='D')
            new_sim.save()
        else:
            # create placeholder-genome_similarity in database, start huey job
            new_sim = GenomeSimilarity(from_genome=from_genome, to_genome=to_genome, similarity=-1, status='R')
            new_sim.save()
            calculate_genome_similarity(g1=from_genome, g2=to_genome)
        return new_sim, True

    def bulk_create(self, objs, *args, **kwargs):
        # ensure from_genome has smaller genome.identifier according to Python lexicographical ordering
        for obj in objs:
            obj.sort()
        return super(GenomeSimilarityManager, self).bulk_create(objs=objs, *args, **kwargs)


class GenomeSimilarity(models.Model):
    """
    Genome similarity calculated using the fast GenDisCal algorithm.
        :param similarity

    The GenomeSimilarity-relationship is symmetrical. Only one object is created for every combination:
        :param from_genome: smaller genome.identifier according to Python lexicographical ordering
        :param to_genome: larger genome.identifier according to Python lexicographical ordering
    """

    objects = GenomeSimilarityManager()

    from_genome = models.ForeignKey('website.GenomeContent', on_delete=models.CASCADE, related_name='from_ani')
    to_genome = models.ForeignKey('website.GenomeContent', on_delete=models.CASCADE, related_name='to_ani')
    similarity = models.FloatField()

    DONE = "D"
    RUNNING = "R"
    FAILED = "F"
    STATUS_CHOICES = ((DONE, 'DONE'), (RUNNING, 'RUNNING'), (FAILED, 'FAILED'))

    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('from_genome', 'to_genome')

    def sort(self):
        self.from_genome, self.to_genome = _sort(self.from_genome, self.to_genome)

    @staticmethod
    def invariant():
        for ani in GenomeSimilarity.objects.all():
            assert ani.from_genome.identifier <= ani.to_genome.identifier, \
                F'ERROR: from_genome {ani.from_genome.identifier} must be <= to_genome {ani.to_genome.identifier}'
