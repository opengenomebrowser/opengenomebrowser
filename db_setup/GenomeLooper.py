import json
import os


class GenomeLooper:
    def __init__(self, db_path):
        self.db_path = db_path

    def loop_genomes(self):
        strains_path = os.path.join(self.db_path, 'strains')
        strain_folders = os.scandir(strains_path)
        for strain_folder in strain_folders:
            current_strain = strain_folder.name
            print(current_strain)

            with open(strain_folder.path + "/strain.json") as file:
                strain_dict = json.loads(file.read())

            assert current_strain == strain_dict["name"], \
                "'name' in strain.json doesn't match folder name: {}".format(strain_folder.path)

            representative_identifier = strain_dict["representative"]
            assert os.path.isdir(strain_folder.path + "/genomes/" + representative_identifier), \
                "Error: Representative doesn't exist! Strain: {}, Representative: {}" \
                    .format(strain_folder.name, representative_identifier)

            for genome_folder in os.scandir(strain_folder.path + "/genomes"):
                current_genome = genome_folder.name
                print("   └── " + current_genome)

                with open(genome_folder.path + "/genome.json") as file:
                    genome_dict = json.loads(file.read())

                assert current_genome.startswith(strain_folder.name), \
                    "genome name '{}' doesn't start with corresponding strain name '{}'.".format(current_genome,
                                                                                                 current_strain)
                assert current_genome == genome_dict["identifier"], \
                    "'name' in genome.json doesn't match folder name: {}".format(genome_folder.path)

                self.process(strain_dict, genome_dict)

    def process(self, strain_dict, genome_dict):
        pass
