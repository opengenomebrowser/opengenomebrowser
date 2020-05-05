import os
from subprocess import run, PIPE


class AssemblyStats:
    """
    Wrapper for https://github.com/sanger-pathogens/assembly-stats

    :returns dictionary: with the following entries:
    {
        'filename': 'path_to_assembly.fasta',
        'total_length': 1836358,
        'number': 62,
        'mean_length': 29618.68,
        'longest': 136567,
        'shortest': 253,
        'N_count': 2,
        'Gaps': 2,
        'N50': 57048,
        'N50n': 11,
        'N70': 38854,
        'N70n': 19,
        'N90': 17985,
        'N90n': 32
    }
    """

    def __init__(self):
        self.assembly_stat_path = os.path.dirname(__file__) + "/executable/assembly-stats"
        # Test if assembly-stats is set up correctly
        assert os.path.isfile(self.assembly_stat_path)

    def get_assembly_stats(self, assembly_path):
        assert os.path.isfile(assembly_path), "path is invalid: ''{}".format(assembly_path)

        subprocess = run([self.assembly_stat_path, '-t', assembly_path], stdout=PIPE, encoding='ascii')

        assert subprocess.returncode == 0

        description, values = subprocess.stdout.strip().split("\n")
        description = description.split("\t")
        assert description == ['filename', 'total_length', 'number', 'mean_length', 'longest', 'shortest', 'N_count',
                               'Gaps', 'N50', 'N50n', 'N70', 'N70n', 'N90', 'N90n']
        values = values.split("\t")

        assert len(description) == len(values) == 14

        dict = {description[i]: values[i] for i in range(len(values))}

        for entry in ['total_length', 'number', 'longest', 'shortest', 'N_count', 'Gaps', 'N50', 'N50n', 'N70', 'N70n',
                      'N90', 'N90n']:
            dict[entry] = int(dict[entry])

        for entry in ['mean_length']:
            dict[entry] = float(dict[entry])

        return dict
