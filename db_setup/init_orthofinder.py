import sys
import os

OGB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(OGB_DIR)

# import django environment to manipulate the Organism and Genome classes
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OpenGenomeBrowser.settings")
from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

from db_setup.FolderLooper import FolderLooper

folder_looper = FolderLooper(settings.GENOMIC_DATABASE)

if __name__ == "__main__":
    FASTA_PATH = settings.ORTHOFINDER_FASTAS
    assert not os.path.isdir(FASTA_PATH), F'Folder already exists! {FASTA_PATH}'
    os.mkdir(FASTA_PATH)

    print('getting links to faas')
    for genome in FolderLooper(settings.GENOMIC_DATABASE).genomes(skip_ignored=True, sanity_check=False, representatives_only=True):
        faa_path = os.path.join(genome.path, genome.json['cds_tool_faa_file'])
        assert os.path.isfile(faa_path), faa_path
        rel_path = os.path.relpath(faa_path, start=FASTA_PATH)
        os.symlink(src=rel_path, dst=F"{FASTA_PATH}/{genome.iden}.faa")

    cmd = F"orthofinder -f /input/OrthoFinder/fastas"

    print('Run orthofinder like this:', cmd)

    container_cmd = F"-it --rm -v {os.path.abspath(settings.GENOMIC_DATABASE)}:/input:Z davidemms/orthofinder {cmd}"

    p_cmd = F"podman run --ulimit=host {container_cmd}"
    print(F'run this command if you use podman:')
    print(F'run this command: {p_cmd}')

    d_cmd = F"docker run --ulimit nofile=1000000:1000000 {container_cmd}"
    print(F'run this command if you use docker:')
    print(F'run this command: {d_cmd}')
