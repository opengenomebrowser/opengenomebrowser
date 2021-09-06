import json
from json.decoder import JSONDecodeError
import os
import sys
from functools import cached_property

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from website.serializers import OrganismSerializer, GenomeSerializer
from db_setup.check_metadata import genome_metadata_is_valid


def set_to_list(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f'Could not serialize {obj}')


class BaseEntity:
    path: str
    json_path: str

    def __init__(self, path: str):
        assert os.path.isdir(path), path
        self.path = path

    @property
    def is_ignored(self):
        return os.path.isfile(f'{self.path}/ignore')

    @property
    def has_json(self):
        try:
            json = self.json
            return True
        except JSONDecodeError:
            return False
        except EnvironmentError:
            return False

    @property
    def json(self):
        with open(self.json_path) as file:
            return json.loads(file.read())

    def sanity_check(self):
        if self.is_ignored:
            return True
        else:
            assert self.has_json, f'{self} :: does not have a (valid) json'

    def replace_json(self, data):
        assert type(data) is dict
        # ensure data is serializable
        try:
            json.dumps(data, default=set_to_list)
        except json.JSONDecodeError as e:
            raise AssertionError(f'Could not save dictionary as json: {e}')


        import shutil
        from datetime import datetime
        date = datetime.now().strftime("%Y_%b_%d_%H_%M_%S")

        # create backup
        bkp_dir = f'{self.path}/.bkp'
        os.makedirs(bkp_dir, exist_ok=True)
        bkp_file = f'{bkp_dir}/{date}_folderlooper_organism.json'
        shutil.move(src=self.json_path, dst=bkp_file)

        # write new file
        assert not os.path.isfile(self.json_path)
        with open(self.json_path, 'w') as f:
            json.dump(data, f, sort_keys=True, indent=4, default=set_to_list)


class MockOrganism(BaseEntity):
    def __init__(self, path: str):
        super().__init__(path)
        self.name = os.path.basename(self.path)
        self.json_path = self.path + "/organism.json"

    def __str__(self):
        return f'<MockOrganism {self.name}>'

    def sanity_check(self):
        super().sanity_check()

        assert self.name == self.json['name'], \
            f"{self} :: 'name' in organism.json doesn't match folder name: {self.path}"

        organism_serializer = OrganismSerializer(data=self.json)
        organism_serializer.is_valid(raise_exception=True)

        representative = self.representative()

        assert representative.identifier.startswith(self.name), \
            f'{self} :: representative identifer must start with organism name'
        assert os.path.isdir(representative.path), \
            F"{self} :: Representative doesn't exist! Representative: {representative}"
        assert not representative.is_ignored, \
            F"{self} :: Representatives may not be ignored! Representative: {representative}, {representative.path}, {representative.is_ignored}"

    @property
    def genomes_path(self):
        return f'{self.path}/genomes'

    @property
    def representative_path(self):
        return f'{self.path}/genomes/{self.json["representative"]}'

    def representative(self, sanity_check=True):
        """returns: MockGenome"""
        representative = MockGenome(path=self.representative_path, organism=self)
        if sanity_check:
            representative.sanity_check()
        return representative

    def genomes(self, skip_ignored: bool, sanity_check=True) -> []:
        """generator, yields [MockGenome]"""
        genomes_folders = os.scandir(self.genomes_path)
        for genome_folder in genomes_folders:
            genome = MockGenome(path=genome_folder.path, organism=self)
            if skip_ignored and genome.is_ignored:
                continue
            if sanity_check:
                genome.sanity_check()
            yield genome


class MockGenome(BaseEntity):
    def __init__(self, path: str, organism: MockOrganism):
        super().__init__(path)
        self.identifier = os.path.basename(self.path)
        self.organism = organism
        self.json_path = self.path + "/genome.json"

    def __str__(self):
        return f'<MockGenome {self.identifier}>'

    def sanity_check(self):
        super().sanity_check()

        assert self.identifier == self.json['identifier'], \
            F"{self} :: 'identifier' in genome.json doesn't match folder name: {self.path}"

        assert self.identifier.startswith(self.organism.name), f'{self} :: identifer must start with organism name'

        genome_metadata_is_valid(data=self.json, path_to_genome=self.path, raise_exception=True)

        with open(f'{self.path}/{self.json["cds_tool_faa_file"]}') as f:
            first_gene = f.readline().lstrip('>')
            first_gene = first_gene.split(' ', 1)[0].rsplit('|', 1)[-1]
            assert first_gene.startswith(f'{self.identifier}_'), f'Gene identifiers must begin with {self.identifier} :: {first_gene}'

        genome_serializer = GenomeSerializer(data=self.json)
        genome_serializer.is_valid(raise_exception=True)


class FolderLooper:
    def __init__(self, db_path):
        self.db_path = db_path

    def organisms(self, skip_ignored: bool, sanity_check=True) -> [MockOrganism]:
        """generator"""
        organism_path = os.path.join(self.db_path, 'organisms')
        organism_folders = os.scandir(organism_path)
        for organism_folder in organism_folders:
            organism = MockOrganism(path=organism_folder.path)
            if skip_ignored and organism.is_ignored:
                continue
            if sanity_check:
                organism.sanity_check()
            yield organism

    def genomes(self, skip_ignored: bool, sanity_check=True, representatives_only=False) -> [MockGenome]:
        """generator"""
        for organism in self.organisms(skip_ignored=skip_ignored, sanity_check=sanity_check):
            if representatives_only:
                yield organism.representative(sanity_check=sanity_check)
            else:
                for genome in organism.genomes(skip_ignored=skip_ignored, sanity_check=sanity_check):
                    yield genome
