from huey.contrib.djhuey import task
from lib.genome_similarity.gendiscal_wrapper import GenDisCal
from lib.orthofinder.orthofinder import Orthofinder
import psutil
import time


@task()
def calculate_genome_similarity(g1, g2) -> float:
    from website.models.GenomeSimilarity import GenomeSimilarity
    from website.models.GenomeContent import GenomeContent
    g1: GenomeContent
    g2: GenomeContent
    # The multiprocessing function must be at the top level of the module for it to work with Django.
    # https://stackoverflow.com/questions/48046862/
    print(F'start GenomeSimilarity calc {g1.identifier} :: {g2.identifier}')

    try:
        sim_score = GenDisCal().calculate_similarity(
            fasta1=g1.genome.assembly_fasta(relative=False),
            fasta2=g2.genome.assembly_fasta(relative=False),
            preset='approxANI'
        )
    except Exception as e:
        sim_obj = GenomeSimilarity.objects.get(from_genome=g1, to_genome=g2)
        if sim_obj.status in ['R', 'F']:
            sim_obj.status = 'F'  # FAILED
            sim_obj.save()
        print(F'ANI failed: {g1.identifier} :: {g2.identifier}')
        raise e

    sim_obj = GenomeSimilarity.objects.get(from_genome=g1, to_genome=g2)
    assert sim_obj.status == 'R'  # RUNNING
    sim_obj.similarity = sim_score
    sim_obj.status = 'D'  # DONE
    sim_obj.save()
    print(F'completed GenomeSimilarity: {g1.identifier} :: {g2.identifier} :: {sim_score}')


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
