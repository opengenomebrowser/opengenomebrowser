import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GenomeLooper:
    def __init__(self, db_path):
        self.db_path = db_path

    def loop_genomes(self, skip_ignored: bool = True):
        organism_path = os.path.join(self.db_path, 'organisms')
        organism_folders = os.scandir(organism_path)
        for organism_folder in organism_folders:
            if skip_ignored and os.path.isfile(F'{organism_folder.path}/.ignore'):
                continue

            current_organism = organism_folder.name
            print(current_organism)

            organism_dict_path = organism_folder.path + "/organism.json"
            with open(organism_dict_path) as file:
                organism_dict = json.loads(file.read())

            assert current_organism == organism_dict["name"], \
                F"'name' in organism.json doesn't match folder name: {organism_folder.path}"

            representative_identifier = organism_dict["representative"]
            assert os.path.isdir(organism_folder.path + "/genomes/" + representative_identifier), \
                F"Error: Representative doesn't exist! organism: {organism_folder.name}, Representative: {representative_identifier}"

            for genome_folder in os.scandir(organism_folder.path + "/genomes"):
                if skip_ignored and os.path.isfile(F'{genome_folder.path}/.ignore'):
                    continue

                current_genome = genome_folder.name
                print("   └── " + current_genome)

                genome_dict_path = genome_folder.path + "/genome.json"
                with open(genome_dict_path) as file:
                    genome_dict = json.loads(file.read())

                assert current_genome.startswith(organism_folder.name), \
                    F"genome name '{current_genome}' doesn't start with corresponding organism name '{current_organism}'."
                assert current_genome == genome_dict["identifier"], \
                    F"'name' in genome.json doesn't match folder name: {genome_folder.path}"

                self.process(organism_dict, genome_dict, organism_dict_path, genome_dict_path)

    def process(self, organism_dict, genome_dict, organism_dict_path, genome_dict_path):
        pass
