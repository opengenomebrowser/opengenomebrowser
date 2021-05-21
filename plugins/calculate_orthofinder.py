import time
import psutil
from huey.contrib.djhuey import task
from lib.orthofinder.orthofinder import Orthofinder


@task()
def calculate_orthofinder(genomes, cache_file: str) -> str:
    # ensure only one orthofinder process is running:
    orthofinder_running = "orthofinder" in (p.name() for p in psutil.process_iter())
    while orthofinder_running:
        time.sleep(5)
        orthofinder_running = "orthofinder" in (p.name() for p in psutil.process_iter())

    from website.models.CoreGenomeDendrogram import CoreGenomeDendrogram
    from website.models.Genome import Genome
    identifiers = sorted(set(g.identifier for g in genomes))
    hash = Genome.hash_genomes(genomes)

    print(F'Start OrthoFinder with identifiers: {identifiers} ({hash})')

    try:
        newick = Orthofinder().run_precomputed(identifiers=identifiers, cache_file=cache_file)
    except Exception as e:
        dendrogram_obj = CoreGenomeDendrogram.objects.get(unique_id=Genome.hash_genomes(genomes))
        if dendrogram_obj.status == 'D':
            return

        dendrogram_obj.status = 'F'  # FAILED
        dendrogram_obj.message = str(e)
        dendrogram_obj.save()
        print(F'OrthoFinder failed: {identifiers}')
        raise e

    dendrogram_obj = CoreGenomeDendrogram.objects.get(unique_id=Genome.hash_genomes(genomes))
    dendrogram_obj.newick = newick
    dendrogram_obj.status = 'D'  # DONE
    dendrogram_obj.save()
    print(F'completed OrthoFinder: {identifiers} :: {newick}')

    CoreGenomeDendrogram.clean_cache()
