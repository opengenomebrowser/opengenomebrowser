#! /usr/bin/python3
import json
import os
from subprocess import run, PIPE
from lib.ncbi_blast.blast_wrapper import MakeBlastDBs


class MemberLooper:
    def __init__(self, db_path):
        self.db_path = db_path

    def loop_members(self):
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
            assert os.path.isdir(strain_folder.path + "/members/" + representative_identifier), \
                "Error: Representative doesn't exist! Strain: {}, Representative: {}" \
                    .format(strain_folder.name, representative_identifier)

            for member_folder in os.scandir(strain_folder.path + "/members"):
                current_member = member_folder.name
                print("   └── " + current_member)

                with open(member_folder.path + "/member.json") as file:
                    member_dict = json.loads(file.read())

                assert current_member.startswith(strain_folder.name), \
                    "Member name '{}' doesn't start with corresponding strain name '{}'.".format(current_member,
                                                                                                 current_strain)
                assert current_member == member_dict["identifier"], \
                    "'name' in member.json doesn't match folder name: {}".format(member_folder.path)

                self.process(strain_dict, member_dict)

    def process(self, strain_dict, member_dict):
        pass


class MemberLooperMakeBlastDB(MemberLooper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mbdb = MakeBlastDBs(blast_path='lib/ncbi_blast/bin')

    def mkblastdbs(self, path_to_member, assembly_fn, faa_fn, ffn_fn, overwrite):
        print(path_to_member)
        assert os.path.isdir(path_to_member), F'Member folder does not exist! {path_to_member}'
        assembly_file = os.path.join(path_to_member, '1_assembly', assembly_fn)
        faa_file = os.path.join(path_to_member, '2_cds', faa_fn)
        ffn_file = os.path.join(path_to_member, '2_cds', ffn_fn)

        for file, dbtype in [(assembly_file, 'nucl'), (faa_file, 'prot'), (ffn_file, 'nucl')]:
            assert os.path.isfile(file), F'File does not exist! {file}'
            self.mbdb.mkblastdb(file=file, dbtype=dbtype, overwrite=overwrite)

    def process(self, strain_dict, member_dict):
        path_to_member = os.path.join(self.db_path, 'strains', strain_dict['name'], 'members',
                                      member_dict['identifier'])
        assembly_fn = member_dict['assembly_fasta_filename']
        faa_fn = member_dict['cds_tool_faa_filename']
        ffn_fn = member_dict['cds_tool_ffn_filename']
        self.mkblastdbs(path_to_member, assembly_fn, faa_fn, ffn_fn, overwrite=False)


if __name__ == "__main__":
    member_looper = MemberLooperMakeBlastDB(db_path='database')
    member_looper.loop_members()
