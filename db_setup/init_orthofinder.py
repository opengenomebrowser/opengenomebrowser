import os
from db_setup.MemberLooper import MemberLooper


class MemberLooperInitOrthofinder(MemberLooper):
    def process(self, strain_dict, member_dict):
        path_to_member = os.path.join(self.db_path, 'strains', strain_dict['name'], 'members',
                                      member_dict['identifier'])
        faa_fn = member_dict['cds_tool_faa_file']
        faa_path = os.path.join(path_to_member, faa_fn)
        assert os.path.isfile(faa_path), faa_path
        rel_path = os.path.relpath(faa_path, start=FASTA_PATH)
        os.symlink(src=rel_path, dst=F"{FASTA_PATH}/{member_dict['identifier']}.faa")


if __name__ == "__main__":
    assert os.path.basename(os.getcwd()) == 'OpenGenomeBrowser', F'CWD must be OpenGenomeBrowser, is {os.getcwd()}'
    DB_PATH = 'database'
    if not os.path.isdir(DB_PATH):
        raise NotADirectoryError(F'database dir not found: {DB_PATH}')

    ORTHOFINDER_PATH = F'{DB_PATH}/OrthoFinder'
    assert not os.path.isdir(ORTHOFINDER_PATH), F'This script is intended to initiate Orthofinder for the first time only! \
To procceed, delete the folder.'

    os.mkdir(ORTHOFINDER_PATH)
    FASTA_PATH = F'{ORTHOFINDER_PATH}/fastas'
    os.mkdir(FASTA_PATH)
    FOLDERPOINTER_PATH = F'{ORTHOFINDER_PATH}/orthofinder_folder.txt'
    open(FOLDERPOINTER_PATH, 'a').close()  # create the file

    print('getting links to faas')
    member_looper = MemberLooperInitOrthofinder(db_path=DB_PATH)
    member_looper.loop_members()

    post_cmd = F"-it --rm -v {os.path.abspath(DB_PATH)}:/input:Z davidemms/orthofinder orthofinder -f /input/OrthoFinder/fastas"

    p_cmd = F"podman run --ulimit=host {post_cmd}"
    print(F'run this command if you use podman:')
    print(F'run this command: {p_cmd}')

    d_cmd = F"docker run --ulimit nofile=1000000:1000000 {post_cmd}"
    print(F'run this command if you use docker:')
    print(F'run this command: {d_cmd}')

    print()
    print(F'Finally, enter the Orthofinder Result date into {FOLDERPOINTER_PATH} (e.g. "Results_May27")')
