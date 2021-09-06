from huey.contrib.djhuey import task
from lib.genome_similarity.gendiscal_wrapper import GenDisCal


@task()
def calculate_gendiscal(g1, g2):
    from website.models.GenomeSimilarity import GenomeSimilarity
    from website.models.GenomeContent import GenomeContent
    g1: GenomeContent
    g2: GenomeContent
    # The multiprocessing function must be at the top level of the module for it to work with Django.
    # https://stackoverflow.com/questions/48046862/
    print(f'start GenomeSimilarity calc {g1.identifier} :: {g2.identifier}')

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
        print(f'ANI failed: {g1.identifier} :: {g2.identifier}')
        raise e

    sim_obj = GenomeSimilarity.objects.get(from_genome=g1, to_genome=g2)
    assert sim_obj.status == 'R'  # RUNNING
    sim_obj.similarity = sim_score
    sim_obj.status = 'D'  # DONE
    sim_obj.save()
    print(f'completed GenomeSimilarity: {g1.identifier} :: {g2.identifier} :: {sim_score}')
