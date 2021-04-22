import os
from io import StringIO
from shutil import rmtree
import contextlib
import tempfile
from subprocess import call, run, PIPE
from Bio import SeqIO
from lib.dot.DotPrep import run as dotprep_run


def is_installed(program):
    """
    Test if a program is installed.

    :param program: path to executable or command
    :return: if program executable: program; else None
    """

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:  # check if path to program is valid
        return is_exe(program)
    else:  # check if program is in PATH
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
        return False


class Nucmer:
    """
    Wrapper for nucmer3: http://mummer.sourceforge.net/
    Requires nucmer to be installed.
    """

    def __init__(self, gendiscal_path=None):
        self.nucmer_path = 'nucmer'
        assert is_installed('nucmer'), f'Nucmer is not installed! {self.nucmer_path}'

        # nucmer works
        assert call([self.nucmer_path, '--version'], stderr=PIPE, stdout=PIPE) == 0, 'Nucmer is not executable!'

    def align(self, fasta_ref: str, fasta_qry: str, work_dir: str, arguments: dict = None) -> str:
        """
        :param fasta_ref: path to first assembly fasta
        :param fasta_qry: path to second assembly fasta
        :param arguments: dict with additional arguments for nucmer, e.g. {'--mincluster': 100}
        :return: str: path to out.delta
        """
        for fasta in [fasta_ref, fasta_qry]:
            assert os.path.isfile(fasta), f'path is invalid: {fasta}'

        assert os.path.isdir(work_dir), f'work_dir does not exist: {work_dir}'

        result_path = f'{work_dir}/out.delta'

        assert not os.path.isfile(result_path), f'result_path already exists: {result_path}'

        cmd = [self.nucmer_path]
        if arguments is not None:
            for arg, val in arguments.items():
                cmd.extend([str(arg), str(val)])
        cmd.extend([os.path.abspath(fasta_ref), os.path.abspath(fasta_qry)])

        subprocess = run(
            cmd,
            cwd=work_dir,
            stdout=PIPE, stderr=PIPE, encoding='ascii')

        error_message = F'Nucmer occurred with fasta_ref={fasta_ref} and fasta_qry={fasta_qry}; stdout={subprocess.stdout}; stderr={subprocess.stderr}'

        assert subprocess.returncode == 0, error_message
        assert os.path.isfile(result_path), error_message
        return result_path


nucmer = Nucmer()


class DotPrepArgs:
    def __init__(self, delta, output_filename, unique_length=10000, max_overview_alignments=1000):
        self.delta = delta
        self.unique_length = unique_length
        self.out = output_filename
        self.overview = max_overview_alignments


class DotPrep:
    @classmethod
    def run(cls, fasta_ref: str, fasta_qry: str, gbk1: str = None, mincluster: int = 65) -> (str, str):
        """
        :param fasta_ref: path to first assembly fasta
        :param fasta_qry: path to second assembly fasta
        :return: coords, index
        """
        for fasta in [fasta_ref, fasta_qry]:
            assert os.path.isfile(fasta), f'path is invalid: {fasta}'

        tempdir = tempfile.TemporaryDirectory()

        delta_path = nucmer.align(fasta_ref=fasta_ref, fasta_qry=fasta_qry, work_dir=tempdir.name, arguments={'--mincluster': mincluster})

        with contextlib.redirect_stdout(StringIO()):
            dotprep_run(DotPrepArgs(delta=delta_path, output_filename=f'{tempdir.name}/out'))

        result_files = os.listdir(tempdir.name)

        assert set(result_files) == {'out.coords.idx', 'out.coords', 'out.uniqueAnchorFiltered_l10000.delta.gz', 'out.delta'}, \
            f'DotPrep failed: result_files are incomplete. {result_files=} {tempdir.name=}'

        with open(f'{tempdir.name}/out.coords') as f:
            coords = f.read()
        with open(f'{tempdir.name}/out.coords.idx') as f:
            index = f.read()

        assert coords.split('\n', 1)[0] == 'ref_start,ref_end,query_start,query_end,ref', f'DotPrep failed: coords incorrect. {coords=}'
        assert index.split('\n', 1)[0] == '#ref', f'DotPrep failed: index incorrect. {index=}'

        tempdir.cleanup()

        return coords, index

    @classmethod
    def gbk_to_annotation_file(cls, gbk: str, is_ref: bool) -> str:
        """
        Turn gbk into Dot-compliant format.

        :param gbk: path to genbank file that corresponds to fasta_ref
        :param is_ref: are the annotations for the reference- or the query sequence?
        :return: dot-compliant annotations string
        """
        if is_ref:
            result = 'ref,ref_start,ref_end,name,strand\n'
        else:
            result = 'query,query_start,query_end,name,strand\n'

        with open(gbk, "r") as input_handle:
            for scf in SeqIO.parse(input_handle, "genbank"):
                for f in scf.features:
                    if 'locus_tag' in f.qualifiers:
                        result += f"{scf.id},{f.location.nofuzzy_start},{f.location.nofuzzy_end},{f.qualifiers['locus_tag'][0]},{'+' if f.strand else '-'}\n"

        return result

    @classmethod
    def gbk_to_annotation(cls, gbk: str, is_ref: bool) -> [dict]:
        """
        Turn gbk into Dot-compliant format.

        :param gbk: path to genbank file that corresponds to fasta_ref
        :param is_ref: are the annotations for the reference- or the query sequence?
        :return: dot-compliant annotations list of dictionaries
        """
        if is_ref:
            ref_or_query = 'ref'
            ref_or_query_start = 'ref_start'
            ref_or_query_end = 'ref_end'
        else:
            ref_or_query = 'query'
            ref_or_query_start = 'query_start'
            ref_or_query_end = 'query_end'

        with open(gbk, "r") as input_handle:
            result = [{
                ref_or_query: scf.id,
                ref_or_query_start: f.location.nofuzzy_start,
                ref_or_query_end: f.location.nofuzzy_end,
                'name': f.qualifiers['locus_tag'][0],
                'strand': '+' if f.strand else '-'
            }
                for scf in SeqIO.parse(input_handle, "genbank")
                for f in scf.features
                if 'locus_tag' in f.qualifiers]

        return result


if __name__ == '__main__':
    fasta_ref = 'database/organisms/FAM21789/genomes/FAM21789-i1-1.1/1_assembly/FAM21789-i1-1.fna'
    gbk_ref = 'database/organisms/FAM21789/genomes/FAM21789-i1-1.1/2_cds/FAM21789-i1-1.1.gbk'
    fasta_qry = 'database/organisms/FAM6135/genomes/FAM6135-i1-1.1/1_assembly/FAM6135-i1-1.fna'
    gbk_qry = 'database/organisms/FAM6135/genomes/FAM6135-i1-1.1/2_cds/FAM6135-i1-1.1.gbk'


    def test_nucmer():
        tmp_dir = '/tmp/test_nucmer'
        if os.path.isdir(tmp_dir):
            rmtree(tmp_dir)
        os.makedirs(tmp_dir)
        res = nucmer.align(
            fasta_ref=fasta_ref, fasta_qry=fasta_qry,
            work_dir=tmp_dir,
            arguments={'--mincluster': 100}
        )
        assert os.path.isfile(res)


    def test_dotprep():
        coords, index = DotPrep.run(fasta_ref=fasta_ref, fasta_qry=fasta_qry, mincluster=65)
        print('######### COORDS #########')
        print(coords[:200])
        print('######### INDEX #########')
        print(index[:200])


    def test_gbk_to_annotation():
        print('######### ANNO: FILE #########')
        annotations = DotPrep.gbk_to_annotation_file(gbk_ref, is_ref=True)
        print(annotations[:200])
        print('######### ANNO: DICT #########')
        annotations = DotPrep.gbk_to_annotation(gbk_ref, is_ref=False)
        print(annotations[:4])


    test_nucmer()
    test_dotprep()
    test_gbk_to_annotation()
