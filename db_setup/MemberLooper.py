import json
import os


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
