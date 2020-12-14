import os
from subprocess import run, PIPE
from OpenGenomeBrowser import settings
import shutil


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


class OrthofinderError(Exception):
    def __init__(self, message):
        self.message = message


class Orthofinder:
    def __init__(self):
        self.orthofinder_bin = F'{settings.ORTHOFINDER_INSTALL_DIR}/orthofinder.py'
        assert is_installed(self.orthofinder_bin), F'OrthoFinder is not installed! Could not run "{self.orthofinder_bin}"'

    def version(self):
        subprocess = self.__run(['-h'])
        return subprocess.stdout.split(' Copyright (C) ')[0].split('version ')[1]

    def __run(self, arguments: [str]):
        command = [self.orthofinder_bin]
        command.extend(arguments)
        subprocess = run(command, stdout=PIPE, stderr=PIPE, encoding='ascii')
        assert subprocess.returncode == 0, F'orthofinder command failed: {command},\n stdout: {subprocess.stdout},\n stderr: {subprocess.stderr}'
        return subprocess

    def run_precomputed(self, identifiers: [str]):
        identifiers = set(identifiers)

        # Note: only one instance of OrthoFinder can run at the same time!
        orthofinder_fastas = settings.ORTHOFINDER_FASTAS
        assert os.path.isdir(orthofinder_fastas), orthofinder_fastas
        precomputed_folder = F'{settings.ORTHOFINDER_LATEST_RUN}/WorkingDirectory'
        assert os.path.isdir(precomputed_folder), precomputed_folder
        species_ids_path = F'{precomputed_folder}/SpeciesIDs.txt'
        assert os.path.isfile(species_ids_path), species_ids_path

        # backup SpeciesIDs.txt
        species_ids_backup = F'{orthofinder_fastas}/SpeciesIDs.txt.backup'
        if not os.path.isfile(species_ids_backup):
            print('Running Orthofinder for the first time.')
            for line in open(species_ids_path).read().strip().split('\n'):
                assert not line.startswith('#'), "No line should be commented when Orthofinder is run for the first time!"
            shutil.copy(src=species_ids_path, dst=species_ids_backup)

        species_ids_backup = open(species_ids_backup).read().strip()
        species_ids = open(species_ids_path).read().strip()

        def extract_identifier(fasta):
            assert fasta.endswith('.faa')
            id, identifier = fasta.split(' ')
            return identifier[:-4]

        # edit species_ids_backup, overwrite species_ids
        old_species_ids = species_ids_backup.split('\n')
        old_identifiers = set(extract_identifier(line) for line in old_species_ids)

        # if old_identifiers == identifiers, simply return the already-computed newick tree.
        if old_identifiers == identifiers:
            return open(F'{orthofinder_fastas}/fastas/OrthoFinder/{precomputed_folder}/Species_Tree/SpeciesTree_rooted.txt').read().strip()

        # raise OrthofinderError if an identifier is not amongst the precomputed fastas
        not_precomputed = identifiers.difference(old_identifiers)
        if len(not_precomputed):
            raise OrthofinderError(F'The following genomes have not been precomputed: {not_precomputed}. Remove them!')

        # comment unwanted fastas
        def filter(line):
            identifier = extract_identifier(line)
            if identifier in identifiers:
                return line
            else:
                return F'# {line}'

        # overwrite SpeciesIDs.txt
        new_species_ids = [filter(line) for line in old_species_ids]
        with open(species_ids_path, 'w') as f:
            f.write('\n'.join(new_species_ids))

        # run Orthofinder
        subprocess = self.__run(['-b', precomputed_folder])

        # print('XXXXXXXXXXXX')
        # print(subprocess.stdout)
        # print('XXXXXXXXXXXX')
        # print(subprocess.stderr)
        # print('XXXXXXXXXXXX')

        # get result_dir from stdout
        stdout = subprocess.stdout.split('\n')
        result_dir = stdout[stdout.index('Results:') + 1].strip()
        assert os.path.isdir(result_dir), F'{subprocess.stdout}\n\n{subprocess.stderr}\n\nCould not find result_dir: {result_dir}'

        # extract newick-tree
        species_tree_file = F'{result_dir}/Species_Tree/SpeciesTree_rooted.txt'
        assert os.path.isfile(species_tree_file), F'{subprocess.stdout}\n\n{subprocess.stderr}\n\nCould not find species tree: {species_tree_file}'
        tree = open(species_tree_file).read().strip()

        # cleanup
        shutil.rmtree(result_dir)

        return tree
