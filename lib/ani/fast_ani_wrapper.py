import os
from subprocess import call, run, PIPE
import tempfile
import multiprocessing as mp
from Bio import SeqIO


class FastANI:
    """
    Wrapper for https://github.com/ParBliSS/FastANI
    Requires ncbi_blast and Java 8.
    """

    def __init__(self):
        self.fast_ani_path = os.path.dirname(__file__) + '/fastANI'
        assert os.path.isfile(self.fast_ani_path)

        # Test if fastANI works
        assert call([self.fast_ani_path, '--version'], stderr=PIPE, stdout=PIPE) == 0, "fastANI doesn't work!"

    def one_to_one(self, fasta1: str, fasta2: str, min_scf_length: int = None) -> float:
        """
        :param fasta1: path to first assembly fasta
        :param fasta2: path to second assembly fasta
        :param min_scf_length: remove scaffolds smaller than this value
        :return: float: RECIPROCAL FastANI similarity score. 1 = 100 %, 0 = 0 %
        """
        for fasta in (fasta1, fasta2):
            assert os.path.isfile(fasta), "path is invalid: '{}'".format(fasta)

        if fasta1 == fasta2:
            return 1

        tempdir = tempfile.TemporaryDirectory()
        fasta1_symlink = os.path.join(tempdir.name, '1_' + os.path.basename(fasta1))
        fasta2_symlink = os.path.join(tempdir.name, '2_' + os.path.basename(fasta2))

        if min_scf_length:
            self.__filter_scfs(os.path.abspath(fasta1), fasta1_symlink, min_scf_length)
            self.__filter_scfs(os.path.abspath(fasta2), fasta2_symlink, min_scf_length)
        else:
            os.symlink(os.path.abspath(fasta1), fasta1_symlink)
            os.symlink(os.path.abspath(fasta2), fasta2_symlink)

        forward = self.__one_way_ani(fasta1_symlink, fasta2_symlink)
        backward = self.__one_way_ani(fasta2_symlink, fasta1_symlink)
        result = (forward + backward) / 2

        tempdir.cleanup()

        assert 0 <= result <= 1

        return result

    def __filter_scfs(self, input_fasta: str, output_fasta: str, min_scf_length):
        # filter fasta
        records = [record for record in SeqIO.parse(input_fasta, "fasta") if len(record) >= min_scf_length]
        print('nrecords left after filtering=', len(records))

        assert len(records) > 0, F'Error while filtering scaffolds: No scaffolds were larger than {min_scf_length}!'

        # write temporary fasta
        with open(output_fasta, 'w')as f:
            SeqIO.write(records, f, 'fasta')

    def __one_way_ani(self, fasta1: str, fasta2: str) -> float:
        # Use temporary file to capture FastANI output.

        outfile = tempfile.NamedTemporaryFile()

        p = run(
            [self.fast_ani_path, '-q', fasta1, '-r', fasta2, '-o', outfile.name],
            stdout=PIPE, stderr=PIPE, encoding='ascii')

        result = outfile.read().decode('utf-8').rstrip().split('\t')

        outfile.flush()

        error_message = F'ANI-error occurred: fasta1={fasta1} fasta2={fasta2}; stdout={p.stdout}; stderr={p.stderr}, outfile={result}'
        assert p.returncode == 0, error_message
        assert len(result) == 5, error_message

        result = float(result[2]) / 100
        assert 0 <= result <= 1, error_message

        return result

    @staticmethod
    def helper_fn(genomes: tuple) -> float:
        fa = FastANI()
        return fa.one_to_one(genomes[0], genomes[1])

    @staticmethod
    def calculate_many_similarities(fasta_tuple_list, ncpu: int = None) -> list:
        """
        :param fasta_tuple_list: [(fasta1, fasta2), (fastaA, fastaB), ...]
        :return: int list of same length as fasta_tuple_list
        """
        if not ncpu:
            ncpu = mp.cpu_count()

        pool = mp.Pool(ncpu)
        return pool.map(FastANI.helper_fn, fasta_tuple_list)


if __name__ == '__main__':
    f1 = 'database/strains/FAM19036/genomes/FAM19036/1_assembly/FAM19036.fna'
    f2 = 'database/strains/FAM19038/genomes/FAM19038/1_assembly/FAM19038.fna'
    f3 = 'database/strains/FAM18356/genomes/FAM18356/1_assembly/FAM18356.fna'
    f4 = 'database/strains/FAM17927/genomes/FAM17927/1_assembly/FAM17927.fna'

    from lib.assembly_stats import AssemblyStats

    a_stats = AssemblyStats()
    for f in (f1, f2, f3, f4):
        print(a_stats.get_assembly_stats(f)['N50'])

    fa = FastANI()

    print('should work:')
    res = fa.one_to_one(f1, f2)
    print(res)
    assert res == fa.one_to_one(f2, f1), 'result is not reciprocal!'

    print('many_similarities:')
    res = fa.calculate_many_similarities([(f1, f2)])
    print(res)

    print('FastANI fails with these files:')
    res = fa.one_to_one(f1, f4, min_scf_length=150000)
    print(res)
