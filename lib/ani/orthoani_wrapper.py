import multiprocessing as mp
import os
import tempfile
from subprocess import call, run, PIPE


class OrthoANI:
    """
    Wrapper for https://www.ezbiocloud.net/tools/orthoani
    Requires ncbi_blast and Java 8.
    """

    def __init__(self, blast_dir=None):
        if not blast_dir:
            self.ncbi_blast_dir = os.path.dirname(__file__) + "/../ncbiblast/ncbi_blast/bin"
        else:
            self.ncbi_blast_dir = blast_dir
        assert os.path.isdir(self.ncbi_blast_dir), F"Blast dir does not exist: {self.ncbi_blast_dir}"

        self.ortho_ani_path = os.path.dirname(__file__) + '/OAT_cmd.jar'
        assert os.path.isfile(self.ortho_ani_path)

        # Test if Java is installed
        assert call(['java', '-version'], stderr=PIPE, stdout=PIPE) == 0, 'ani requires Java 8!'

    def calculate_similarity(self, fasta1: str, fasta2: str, ncpu: int = None) -> float:
        """
        :param fasta1: path to first assembly fasta
        :param fasta2: path to second assembly fasta
        :return: float: ani similarity score. 1 = 100 %, 0 = 0 %
        """
        assert os.path.isfile(fasta1), "path is invalid: '{}'".format(fasta1)
        assert os.path.isfile(fasta2), "path is invalid: '{}'".format(fasta2)

        if fasta1 == fasta2: return 1

        if not ncpu:
            ncpu = os.cpu_count()

        # Use temporary folder in order to avoid pollution with unnecessary files.
        # These files may also break future OAT runs.

        tempdir = tempfile.TemporaryDirectory()
        fasta1_symlink = os.path.join(tempdir.name, '1_' + os.path.basename(fasta1))
        fasta2_symlink = os.path.join(tempdir.name, '2_' + os.path.basename(fasta2))
        os.symlink(os.path.abspath(fasta1), fasta1_symlink)
        os.symlink(os.path.abspath(fasta2), fasta2_symlink)

        subprocess = run(
            ['java', '-jar', self.ortho_ani_path,
             '-blastplus_dir', self.ncbi_blast_dir,
             '-num_threads', str(ncpu),
             '-fasta1', fasta1_symlink,
             '-fasta2', fasta2_symlink],
            stdout=PIPE, stderr=PIPE, encoding='ascii')

        tempdir.cleanup()

        error_message = F'ANI-error occurred with fasta1={fasta1} and fasta2={fasta2}; stdout={subprocess.stdout}; stderr={subprocess.stderr}'

        assert subprocess.returncode == 0, error_message

        result = subprocess.stdout.strip().split("\n")

        assert result[-3] == "SUCCESS: true", error_message
        assert result[-1].startswith('OrthoANI : '), error_message
        assert result[-1].endswith(' (%)'), error_message

        result = result[-1][11:-4]

        return float(result) / 100

    @staticmethod
    def calculate_many_similarities(fasta_tuple_list) -> list:
        """
        :param fasta_tuple_list: [(fasta1, fasta2), (fastaA, fastaB), ...]
        :return: int list of same length as fasta_tuple_list
        """

        def calculate_one(two_genomes) -> float:
            return OrthoANI().calculate_similarity(two_genomes[0], two_genomes[1], ncpu=2)

        pool = mp.Pool(mp.cpu_count())
        return pool.map(calculate_one, fasta_tuple_list)


if __name__ == '__main__':
    oa = OrthoANI()
    print(os.getcwd())
    res = oa.calculate_similarity('../../database/strains/FAM13496/genomes/FAM13496-i1-1.1/1_assembly/FAM13496-i1-1.fna',
                                  '../../database/strains/FAM18815/genomes/FAM18815-i1-1.1/1_assembly/FAM18815-i1-1.fna')
    print(res)
