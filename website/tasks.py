import time

from huey import crontab
from huey.contrib.djhuey import task, periodic_task, db_task
from lib.ortho_ani.ortho_ani_wrapper import OrthoANI
from lib.orthofinder.orthofinder import Orthofinder


# def tprint(s, c=32):
#     # Helper to print messages from within tasks using color, to make them
#     # stand out in examples.
#     print('\x1b[1;%sm%s\x1b[0m' % (c, s))


# Tasks used in examples.


@task()
def calculate_ani(g1, g2) -> float:
    from website.models.ANI import ANI
    from website.models.GenomeContent import GenomeContent
    g1: GenomeContent
    g2: GenomeContent
    # The multiprocessing function must be at the top level of the module for it to work with Django.
    # https://stackoverflow.com/questions/48046862/
    print(F'start ANI calc {g1.identifier} :: {g2.identifier}')

    try:
        ani_score = OrthoANI().calculate_similarity(g1.genome.assembly_fasta(relative=False), g2.genome.assembly_fasta(relative=False), ncpu=8)
    except Exception as e:
        ani_obj = ANI.objects.get(from_genome=g1, to_genome=g2)
        if ani_obj.status in ['R', 'F']:
            ani_obj.status = 'F'  # FAILED
            ani_obj.save()
        print(F'ANI failed: {g1.identifier} :: {g2.identifier}')
        raise e

    ani_obj = ANI.objects.get(from_genome=g1, to_genome=g2)
    assert ani_obj.status == 'R'  # RUNNING
    ani_obj.similarity = ani_score
    ani_obj.status = 'D'  # DONE
    ani_obj.save()
    print(F'completed ANI: {g1.identifier} :: {g2.identifier} :: {ani_score}')


@task()
def calculate_orthofinder(genomes) -> str:
    from website.models.GenomeContent import GenomeContent
    from website.models.CoreGenomeDendrogram import CoreGenomeDendrogram
    identifiers = sorted(set(g.identifier for g in genomes))

    print(F'Start OrthoFinder with identifiers: {identifiers}')

    try:
        newick = Orthofinder().run_precomputed(identifiers=identifiers)
    except Exception as e:
        dendrogram_obj = CoreGenomeDendrogram.objects.get(unique_id=CoreGenomeDendrogram.hash_genomes(genomes))
        if dendrogram_obj.status in ['R', 'F']:
            dendrogram_obj.status = 'F'  # FAILED
            dendrogram_obj.save()
        print(F'OrthoFinder failed: {identifiers}')
        raise e

    dendrogram_obj = CoreGenomeDendrogram.objects.get(unique_id=CoreGenomeDendrogram.hash_genomes(genomes))
    assert dendrogram_obj.status == 'R'  # RUNNING
    dendrogram_obj.newick = newick
    dendrogram_obj.status = 'D'  # DONE
    dendrogram_obj.save()
    print(F'completed OrthoFinder: {identifiers} :: {newick}')

    return newick

# @db_task()  # Opens DB connection for duration of task.
# def slow(n):
#     tprint('going to sleep for %s seconds' % n)
#     time.sleep(n)
#     tprint('finished sleeping for %s seconds' % n)
#     return n
#
#
# @task(retries=1, retry_delay=5, context=True)
# def flaky_task(task=None):
#     if task is not None and task.retries == 0:
#         tprint('flaky task succeeded on retry.')
#         return 'succeeded on retry.'
#     tprint('flaky task is about to raise an exception.', 31)
#     raise Exception('flaky task failed!')


# # Periodic tasks.
#
# @periodic_task(crontab(minute='*/2'))
# def every_other_minute():
#     tprint('This task runs every 2 minutes.', 35)
#
#
# @periodic_task(crontab(minute='*/5'))
# def every_five_mins():
#     tprint('This task runs every 5 minutes.', 34)
