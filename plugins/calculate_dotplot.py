from dot import DotPrep
from OpenGenomeBrowser.settings import FOLDER_STRUCTURE, CACHE_DIR, CACHE_MAXSIZE
from lib.ogb_cache.ogb_cache import ogb_cache, timedelta


@ogb_cache(cache_root=CACHE_DIR, maxsize=CACHE_MAXSIZE, wait_tolerance=timedelta(minutes=1))
def calculate_dotplot(fasta_ref: str, fasta_qry: str, mincluster: int):
    coords, index = DotPrep().run_python(
        fasta_ref=f'{FOLDER_STRUCTURE}/{fasta_ref}',
        fasta_qry=f'{FOLDER_STRUCTURE}/{fasta_qry}',
        mincluster=mincluster
    )
    flipped_scaffolds = DotPrep._get_flipped_scaffolds(index=index)
    return coords, index, flipped_scaffolds
