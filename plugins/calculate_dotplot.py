from lib.dot.dot_prep_wrapper import DotPrep
from OpenGenomeBrowser.settings import GENOMIC_DATABASE
from functools import lru_cache


@lru_cache(maxsize=10)  # cache last 10 results
def calculate_dotplot(fasta_ref: str, fasta_qry: str, mincluster: int):
    coords, index = DotPrep.run(
        fasta_ref=f'{GENOMIC_DATABASE}/{fasta_ref}',
        fasta_qry=f'{GENOMIC_DATABASE}/{fasta_qry}',
        mincluster=mincluster
    )
    return coords, index
