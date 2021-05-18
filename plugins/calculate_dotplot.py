from lib.dot.dot_prep_wrapper import DotPrep
from OpenGenomeBrowser.settings import GENOMIC_DATABASE, CACHE_DIR, CACHE_MAXSIZE
from lib.ogb_cache.ogb_cache import ogb_cache, timedelta


@ogb_cache(cache_root=CACHE_DIR, maxsize=CACHE_MAXSIZE, wait_tolerance=timedelta(minutes=1))
def calculate_dotplot(fasta_ref: str, fasta_qry: str, mincluster: int):
    coords, index = DotPrep.run(
        fasta_ref=f'{GENOMIC_DATABASE}/{fasta_ref}',
        fasta_qry=f'{GENOMIC_DATABASE}/{fasta_qry}',
        mincluster=mincluster
    )
    return coords, index
