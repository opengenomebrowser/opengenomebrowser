import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_setup.MemberLooper import MemberLooper
from lib.ncbiblast.ncbi_blast.blast_wrapper import Blast


class MemberLooperMakeBlastDB(MemberLooper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blast = Blast()

    def mkblastdbs(self, path_to_member, assembly_fn, faa_fn, ffn_fn, overwrite):
        print(path_to_member)
        assert os.path.isdir(path_to_member), F'Member folder does not exist! {path_to_member}'
        assembly_file = os.path.join(path_to_member, assembly_fn)
        faa_file = os.path.join(path_to_member, faa_fn)
        ffn_file = os.path.join(path_to_member, ffn_fn)

        for file, dbtype in [(assembly_file, 'nucl'), (faa_file, 'prot'), (ffn_file, 'nucl')]:
            assert os.path.isfile(file), F'File does not exist! {file}'
            self.blast.mkblastdb(file=file, dbtype=dbtype, overwrite=overwrite)

    def process(self, strain_dict, member_dict):
        path_to_member = os.path.join(self.db_path, 'strains', strain_dict['name'], 'members',
                                      member_dict['identifier'])
        assembly_fn = member_dict['assembly_fasta_file']
        faa_fn = member_dict['cds_tool_faa_file']
        ffn_fn = member_dict['cds_tool_ffn_file']
        self.mkblastdbs(path_to_member, assembly_fn, faa_fn, ffn_fn, overwrite=False)


if __name__ == "__main__":
    def run(db_path='database'):
        member_looper = MemberLooperMakeBlastDB(db_path=db_path)
        member_looper.loop_members()


    import fire

    fire.Fire(run)
