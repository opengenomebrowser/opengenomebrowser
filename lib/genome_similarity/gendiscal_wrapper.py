import os
from subprocess import call, run, PIPE
import multiprocessing as mp


class GenDisCal:
    """
    Wrapper for https://github.com/LM-UGent/GenDisCal
    No dependencies!
    """

    def __init__(self, gendiscal_path=None):
        self.gendiscal_path = os.path.dirname(__file__) + '/GenDisCal' if gendiscal_path is None else gendiscal_path
        assert os.path.isfile(self.gendiscal_path)

        # GenDisCal works
        assert call([self.gendiscal_path, '--version'], stderr=PIPE, stdout=PIPE) == 0, 'GenDisCal is not executable!'

    def calculate_similarity(self, fasta1: str, fasta2: str, preset='PaSiT6') -> float:
        """
        :param fasta1: path to first assembly fasta
        :param fasta2: path to second assembly fasta
        :param preset: [PaSiT4, PaSiT6, TETRA, approxANI, combinedSpecies]
        :return: float: genome_similarity similarity score. 1 = 100 %, 0 = 0 %
        """
        for fasta in [fasta1, fasta2]:
            assert os.path.isfile(fasta), "path is invalid: '{}'".format(fasta)

        if fasta1 == fasta2: return 1

        subprocess = run(
            [self.gendiscal_path,
             '--preset', preset,
             fasta1,
             fasta2],
            stdout=PIPE, stderr=PIPE, encoding='ascii')

        error_message = F'ANI-error occurred with fasta1={fasta1} and fasta2={fasta2}; stdout={subprocess.stdout}; stderr={subprocess.stderr}'

        assert subprocess.returncode == 0, error_message

        result = subprocess.stdout.strip().split("\n")

        assert len(result) == 2, error_message
        assert result[0] == 'File1,File2,Expected_Relation,Distance', error_message

        result = result[1].split(',')

        assert len(result) == 4, error_message

        result = result[3]

        return 1 - float(result)

    @staticmethod
    def calculate_many_similarities(fasta_tuple_list, preset='PaSiT6') -> list:
        """
        :param fasta_tuple_list: [(fasta1, fasta2), (fastaA, fastaB), ...]
        :param preset: [PaSiT4, PaSiT6, TETRA, approxANI, combinedSpecies]
        :return: int list of same length as fasta_tuple_list
        """

        def calculate_one(two_genomes) -> float:
            return GenDisCal().calculate_similarity(two_genomes[0], two_genomes[1], preset=preset)

        pool = mp.Pool(mp.cpu_count())
        return pool.map(calculate_one, fasta_tuple_list)


if __name__ == '__main__':
    oa = GenDisCal()
    print(os.getcwd())
    res = oa.calculate_similarity('../../database/organisms/FAM13496/genomes/FAM13496-i1-1.1/1_assembly/FAM13496-i1-1.fna',
                                  '../../database/organisms/FAM18815/genomes/FAM18815-i1-1.1/1_assembly/FAM18815-i1-1.fna')
    print(res)
