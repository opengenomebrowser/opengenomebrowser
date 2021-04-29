from lib.ncbiblast.ncbi_blast.blast_wrapper import Blast
from OpenGenomeBrowser.settings import GENOMIC_DATABASE


def calculate_blast(fasta_string: str, db: [], mode):
    blast = Blast(system_blast=True, outfmt=5)
    db = [f'{GENOMIC_DATABASE}/{f}' for f in db]
    blast_output = blast.blast(fasta_string=fasta_string, db=db, mode=mode)
    return blast_output
