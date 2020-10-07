from huey.contrib.djhuey import task
from lib.orthofinder.orthofinder import Orthofinder
import psutil
import time


@task()
def calculate_orthofinder(genomes) -> str:
    # ensure only one orthofinder process is running:
    orthofinder_running = "orthofinder" in (p.name() for p in psutil.process_iter())
    while orthofinder_running:
        time.sleep(5)
        orthofinder_running = "orthofinder" in (p.name() for p in psutil.process_iter())

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
