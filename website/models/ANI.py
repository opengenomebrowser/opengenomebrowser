from django.db import models
from website.tasks import calculate_ani


def _sort(genome1, genome2):
    # return "smaller" genome first
    if genome1.identifier < genome2.identifier:
        return genome1, genome2
    else:
        return genome2, genome1


class QuestionQuerySet(models.query.QuerySet):
    def get(self, from_genome, to_genome, **kwargs):
        from_genome, to_genome = _sort(from_genome, to_genome)
        return super(QuestionQuerySet, self).get(from_genome=from_genome, to_genome=to_genome, **kwargs)


class AniManager(models.Manager.from_queryset(QuestionQuerySet)):
    def get_or_create(self, from_genome, to_genome, **kwargs):
        from_genome, to_genome = _sort(from_genome, to_genome)

        # return if exists
        try:
            return super(AniManager, self).get(from_genome=from_genome, to_genome=to_genome, **kwargs), False
        except ANI.DoesNotExist:
            pass

        # create if similarity was specified
        if 'similarity' in kwargs:
            return super(AniManager, self).get_or_create(from_genome=from_genome, to_genome=to_genome, similarity=1,
                                                         status='D')

        if from_genome == to_genome:
            # similarity must be 1
            new_ani = ANI(from_genome=from_genome, to_genome=to_genome, similarity=1, status='D')
            new_ani.save()
        else:
            # create placeholder-ani in database, start huey job
            new_ani = ANI(from_genome=from_genome, to_genome=to_genome, similarity=-1, status='R')
            new_ani.save()
            calculate_ani(g1=from_genome, g2=to_genome)
        return new_ani, True

    def bulk_create(self, objs, *args, **kwargs):
        # ensure from_genome has smaller genome.identifier according to Python lexicographical ordering
        for obj in objs:
            obj.sort()
        return super(AniManager, self).bulk_create(objs=objs, *args, **kwargs)


class ANI(models.Model):
    """
    Genome similarity calculated using the fast OrthoANI algorithm.
        :param similarity

    The ANI-relationship is symmetrical. Only one object is created for every combination:
        :param from_genome: smaller genome.identifier according to Python lexicographical ordering
        :param to_genome: larger genome.identifier according to Python lexicographical ordering
    """

    objects = AniManager()

    from_genome = models.ForeignKey('Genome', on_delete=models.CASCADE, related_name='from_ani')
    to_genome = models.ForeignKey('Genome', on_delete=models.CASCADE, related_name='to_ani')
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
        for ani in ANI.objects.all():
            assert ani.from_genome.identifier <= ani.to_genome.identifier, \
                F'ERROR: from_genome {ani.from_genome.identifier} must be <= to_genome {ani.to_genome.identifier}'
