import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_setup.GenomeLooper import GenomeLooper
from lib.ncbiblast.ncbi_blast.blast_wrapper import Blast


class GenomeLooperMakeBlastDB(GenomeLooper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blast = Blast()

    def mkblastdbs(self, path_to_genome, assembly_fn, faa_fn, ffn_fn, overwrite):
        print(path_to_genome)
        assert os.path.isdir(path_to_genome), F'Genome folder does not exist! {path_to_genome}'
        assembly_file = os.path.join(path_to_genome, assembly_fn)
        faa_file = os.path.join(path_to_genome, faa_fn)
        ffn_file = os.path.join(path_to_genome, ffn_fn)

        for file, dbtype in [(assembly_file, 'nucl'), (faa_file, 'prot'), (ffn_file, 'nucl')]:
            assert os.path.isfile(file), F'File does not exist! {file}'
            self.blast.mkblastdb(file=file, dbtype=dbtype, overwrite=overwrite)

    def process(self, strain_dict, genome_dict):
        path_to_genome = os.path.join(self.db_path, 'strains', strain_dict['name'], 'genomes',
                                      genome_dict['identifier'])
        assembly_fn = genome_dict['assembly_fasta_file']
        faa_fn = genome_dict['cds_tool_faa_file']
        ffn_fn = genome_dict['cds_tool_ffn_file']
        self.mkblastdbs(path_to_genome, assembly_fn, faa_fn, ffn_fn, overwrite=False)


if __name__ == "__main__":
    def run(db_path='database'):
        genome_looper = GenomeLooperMakeBlastDB(db_path=db_path)
        genome_looper.loop_genomes()


    import fire

    fire.Fire(run)
