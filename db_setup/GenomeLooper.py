import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GenomeLooper:
    def __init__(self, db_path):
        self.db_path = db_path

    def loop_genomes(self):
        organism_path = os.path.join(self.db_path, 'organism')
        organism_folders = os.scandir(organism_path)
        for organism_folder in organism_folders:
            current_organism = organism_folder.name
            print(current_organism)

            with open(organism_folder.path + "/organism.json") as file:
                organism_dict = json.loads(file.read())

            assert current_organism == organism_dict["name"], \
                "'name' in organism.json doesn't match folder name: {}".format(organism_folder.path)

            representative_identifier = organism_dict["representative"]
            assert os.path.isdir(organism_folder.path + "/genomes/" + representative_identifier), \
                "Error: Representative doesn't exist! organism: {}, Representative: {}" \
                    .format(organism_folder.name, representative_identifier)

            for genome_folder in os.scandir(organism_folder.path + "/genomes"):
                current_genome = genome_folder.name
                print("   └── " + current_genome)

                with open(genome_folder.path + "/genome.json") as file:
                    genome_dict = json.loads(file.read())

                assert current_genome.startswith(organism_folder.name), \
                    "genome name '{}' doesn't start with corresponding organism name '{}'.".format(current_genome,
                                                                                                 current_organism)
                assert current_genome == genome_dict["identifier"], \
                    "'name' in genome.json doesn't match folder name: {}".format(genome_folder.path)

                self.process(organism_dict, genome_dict)

    def process(self, organism_dict, genome_dict):
        pass
