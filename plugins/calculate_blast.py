from lib.ncbiblast.ncbi_blast.blast_wrapper import Blast
from OpenGenomeBrowser.settings import GENOMIC_DATABASE, CACHE_DIR, CACHE_MAXSIZE
from lib.ogb_cache.ogb_cache import ogb_cache, timedelta


@ogb_cache(cache_root=CACHE_DIR, maxsize=CACHE_MAXSIZE, wait_tolerance=timedelta(seconds=30))
def calculate_blast(fasta_string: str, db: tuple, mode: str):
    blast = Blast(system_blast=True, outfmt=5)
    db = [f'{GENOMIC_DATABASE}/{f}' for f in db]
    blast_output = blast.blast(fasta_string=fasta_string, db=db, mode=mode)
    return blast_output
