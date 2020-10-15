# OpenGenomeBrowser

**ALERT: This software is still under development! If you want to try it out, contact the developer first!**

**Prototype:** [opengenomebrowser.bioinformatics.unibe.ch](https://opengenomebrowser.bioinformatics.unibe.ch/)

To talk to the developer informally, join the OpenGenomeBrowser [Discord channel](https://discord.gg/mDm4fqf).
<hr>

_OpenGenomeBrowser is a dynamic and scalable web platform for comparative genomics._

-   OpenGenomeBrowser automates simple bioinformatics steps:
    - Dendrograms (Taxid-based, ANI-based and OrthoFinder-based)
    - Searching for annotations in genomes
    - Visualizing genomes on KEGG maps
    - BLAST
    - Visualisation of gene loci
-   OpenGenomeBrowser has few prerequisites:
    - Genome files must be stored in certain folder structure
    - One metadata file for each genome and organism
-   OpenGenomeBrowser is flexible:
    - Orthofinder is recommended, but not required
    - Computationally intensive processes can be outsourced to a cluster

<div align="center">
<img src="/website/static/global/customicons/ogb-full.svg"  width="500px">
</div>

### Key concepts

-   _Organism_: biological entity
-   _Genome_: sequencing variant
-   _Representative_: best genome of organism



## Get help
If you find a bug that has not already been reported, submit an issue on this github.

If you want to chat, contact me via [Discord](https://discord.gg/mDm4fqf).



## Prerequisites

### Folder structure

```
└── organisms
     ├── ORGANISM1
     ├── ...
     └── EXAMPLE1234
         ├── organism.json
         └── genomes
            ├── EXAMPLE1234-1-1.1
            └── EXAMPLE1234-2-1.1
              ├── genome.json
              ├── assembly.fna
              ├── protein.faa
              ├── genbank.gbk
              ├── generalfeatureformat.gff
              ├── annotations.ko
              └── annotations.eggnog
```

##### Notes:

-   genome names must start with the name of the corresponding organism
    -   we _suggest_ to use this suffix format:
        `organism`-`isolate`-`assembly`.`annotation`
    -   example: organism=`EXAMPLE1234` -> `EXAMPLE1234-2-1.1`
-   gene locus tags must start with the genome identifier, then an underline (`_`)
    -   example: `EXAMPLE1234-2-1.1_000001`
    
### Metadata (NOTE: these specifications are not final!)

##### Notes:
-    paths are relative to the genome folder, i.e. it's fine to have files in a subfolders of the genome folder
-    date format: `"%Y-%m-%d"`, i.e. `2000-12-31`

##### organism.json:

(all mandatory fields have dummy data, all non-mandatory fields have the expected null-input)

```json
{
    "name": "EXAMPLE1234",
    "alternative_name": null,
    "taxid": null,
    "restricted": false,
    "tags": [],
    "representative": "EXAMPLE1234-2-1.1"
}
```

##### genome.json:

(all mandatory fields have dummy data, all non-mandatory fields have the expected null-input)

```json
{
    "identifier": "EXAMPLE1234-2-1.1",
    "contaminated": false,
    "old_identifier": null,
    "isolation_date": null,
    "env_broad_scale": [],
    "env_local_scale": [],
    "env_medium": [],
    "growth_condition": null,
    "geographical_coordinates": null,
    "geographical_name": null,
    "sequencing_tech": null,
    "sequencing_tech_version": null,
    "sequencing_date": null,
    "sequencing_coverage": null,
    "assembly_tool": null,
    "assembly_version": null,
    "assembly_date": null,
    "nr_replicons": null,
    "cds_tool": null,
    "cds_tool_date": null,
    "cds_tool_version": null,
    "cds_tool_faa_file": "protein.faa",
    "cds_tool_gbk_file": "genbank.gbk",
    "cds_tool_gff_file": "generalfeatureformat.gff",
    "cds_tool_sqn_file": null,
    "cds_tool_ffn_file": null,
    "assembly_fasta_file": "assembly.fna",
    "custom_annotations": [],
    "BUSCO": {},
    "bioproject_accession": null,
    "biosample_accession": null,
    "genome_accession": null,
    "literature_references": [],
    "custom_tables": {},
    "tags": []
}
```

##### BUSCO format:
```
"BUSCO": {
    "C": 0,
    "D": 0,
    "F": 0,
    "M": 0,
    "S": 0,
    "T": 0
}
```

##### Custom annotations format - type eggnog:
```
"custom_annotations": [
        {
            "date": "0000-00-00",
            "file": "annotations.eggnog",
            "type": "eggnog"
        }
    ]
```
The file `annotations.eggnog` must be an eggNOG-mapper v2 output file. (Usual filename: `query_seqs.fa.emapper.annotations`)

##### Custom annotations format - type tsv:
```
"custom_annotations": [
        {
            "date": "0000-00-00",
            "file": "annotations.ko",
            "type": "KEGG"  # allowed types: "KEGG", "GO", "R", "EC", "custom"
        }
    ]
```
A valid custom_annotations file must be in this format: `locustag\tannotation1, annotation2, annotation3`
 
I.e., this would be a valid file:
```
EXAMPLE1234-2-1.1_000001	K000001
EXAMPLE1234-2-1.1_000004
EXAMPLE1234-2-1.1_000008	K000001, K000002
```

##### Custom tables format:
```
"custom_tables": {
    "Table 1 Title": {
        "index_col": "taxid",
        "taxid_cols": ["taxid"],
        "rows": [
            {
                "description": "Fakebacillus bullshitingis organism 42 16S ribosomal RNA, partial sequence",
                "taxid": 0,
                "evalue": 0.0
            }
        ]
    }
}
```

### OrthoFinder (recommended, not required)

OrthoFinder can be found [here](https://github.com/davidemms/OrthoFinder).

If you choose to add OrthoFinder, prepare as follows (can be done automatically using `db_setup/init_orthofinder.py`):
```
├── organisms
    └── ...
└── OrthoFinder
     └── fastas
         ├── <genome-identifier>.faa -> ../../organisms/.../genomes/<genome-identifier>/protein.faa
         ├── <genome-identifier>.faa -> ../../organisms/.../genomes/<genome-identifier>/protein.faa
         └── ...
```

-   Link (or copy) all protein fastas you want to be available for OrthoFinder-based trees and orthogroup annotations
into the folder `OrthoFinder/fastas`.
-   In other words, if your database is very big, you could exclude non-representative and contaminated genomes, for 
example.
-   The fastas **must** be named as follows: `<genome-identifier>.faa`
-   Run OrthoFinder (`orthofinder -f /path/to/OrthoFinder/fastas`)
-   The great thing about OrthoFinder is that one can add or remove species efficiently, by recycling previous 
pairwise comparisons. See [OrthoFinder docs](https://github.com/davidemms/OrthoFinder#advanced-usage) for more 
information.
-   In `settings.py`, define the variables `settings.ORTHOFINDER_BASE`, `settings.ORTHOFINDER_LATEST_RUN` and 
`settings.ORTHOFINDER_FASTA_ENDINGS`.

When OrthoFinder is done, the folder structure should look like this:
```
└── organisms
    └── ...
└── OrthoFinder
     └── fastas
         ├── ...
         └── OrthoFinder
             └── ...
```

### Ortholog annotations

Ortholog annotations are handled differently than regular annotations. The reason is that it would be unnatural and 
unnecessarily complicated to take the single ortholog annotation file, split it into one file per genome, distribute
it into the folder structure, and adapt all metadata files.

Instead, OpenGenomeBrowser expects one file that links ortholog identifiers with genes, like this:
```
N0.HOG0000000	genome_1_123, genome_2_234
N0.HOG0000001	genome_2_345, genome_3_456, genome_4_567
N0.HOG0000002	genome_6_789, genome_7_890
```

In addition, another file can be provided that links ortholog identifiers with descriptions, like this:
```
N0.HOG0000000	amino acid ABC transporter ATP-binding protein
N0.HOG0000001	winged helix-turn-helix transcriptional regulator
N0.HOG0000002	DNA topoisomerase (ATP-hydrolyzing) subunit B
```

If this information is not available, use an empty file.

Note: this file must be sorted! This can be done like this:
`LC_ALL=C sort --key=1 --field-separator=$'\t' --output=file.txt.sorted file.txt`

I wrote a [script](https://gitlab.bioinformatics.unibe.ch/troder/orthofinder_tools/-/blob/master/simplify_orthologs.py) 
that turns Orthofinder output into this format.



## Set-up (to be simplified)

### Basic steps

1.   install dependencies
1.   create Python 3.6+ venv
1.   create Postgresql 10+ database
1.   clone this repository, adapt settings
1.   populate Postgresql database
1.   configure nginx and uwsgi (for deployment only)

### Example commands (Note: these commands were used on CentOS 8

##### 1. install dependencies

```
sudo dnf config-manager --set-enabled PowerTools
sudo dnf install git gcc
sudo dnf install python38 python38-devel python38-numpy python38-setuptools python38-wheel
sudo dnf install postgresql postgresql-devel postgresql-server libpq-devel python3-psycopg2 pcre-devel
# these packages may have other names in other operating systems!

# NCBI BLAST
sudo dnf install libnsl perl-List-MoreUtils perl-File-Temp perl-Archive-Tar
BLAST_RPM='ncbi-blast-2.10.1+-1.x86_64.rpm'  # adapt path to current blast executable
wget https://ftp.ncbi.nlm.nih.gov/blast/executables/LATEST/${BLAST_RPM}
sudo rpm -i $BLAST_RPM

# Clustal Omega
wget http://www.clustal.org/omega/clustalo-1.2.4-Ubuntu-x86_64 -O /usr/bin/clustalo
chmod +x /usr/bin/clustalo

# MAFFT
wget https://mafft.cbrc.jp/alignment/software/mafft-7.471-gcc_fc6.x86_64.rpm
sudo rpm -i mafft-7.471-gcc_fc6.x86_64.rpm

# Muscle
wget https://www.drive5.com/muscle/downloads3.8.31/muscle3.8.31_i86linux64.tar.gz
tar -xvf muscle3.8.31_i86linux64.tar.gz
sudo mv muscle3.8.31_i86linux64 /usr/bin/muscle

# OrthoFinder
wget https://github.com/davidemms/OrthoFinder/releases/download/2.3.12/OrthoFinder.tar.gz
tar -xvf OrthoFinder.tar.gz
sudo cp -r OrthoFinder /opt/    
```

##### 2. create Python 3.6+ venv (in an appropriate location)

```
python3.8 -m venv ogb-venv
source ogb-venv/bin/activate
pip install --upgrade pip
```

##### 3. create Postgresql 10+ database

```shell script
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo passwd postgres  # set password for postgres user
sudo su - postgres
[as user postgres]$ initdb -D open_genome_browser
[as user postgres]$ systemctl restart postgresql.service
[as user postgres]$ createuser --encrypted --pwprompt ogb_admin  # set secure password!
[as user postgres]$ createdb --owner=ogb_admin open_genome_browser_db
[as user postgres]$ exit
```

Test if you can connect to the database:

```
sudo systemctl restart postgresql.service
psql -d open_genome_browser_db -U ogb_admin
$ open_genome_browser_db=> \quit
```
If it does not work, try adjusting `/var/lib/pgsql/data/pg_hba.conf`: add this line:
```text
local   all             ogb_admin                               md5
```
(see [stackoverflow](https://stackoverflow.com/questions/18664074/getting-error-peer-authentication-failed-for-user-postgres-when-trying-to-ge)))

Note: if you mess up and want to start fresh, this is how to drop and recreate the database:

```
# NOTE: this deletes ALL data in open_genome_browser_db!
sudo su - postgres
[as user postgres]$ dropdb open_genome_browser_db
[as user postgres]$ createdb open_genome_browser_db --owner ogb_admin
[as user postgres]$ exit
# note: now re-run "python manage.py makemigrations && python manage.py migrate" to recreate the database schemes
```

##### 4. clone this repository (into an appropriate location), adapt settings

```
git clone https://gitlab.bioinformatics.unibe.ch/troder/opengenomebrowser.git
cd opengenomebrowser
git submodule update --init --recursive
pip install -r requirements.txt  # ensure you are in the previously created venv!
```

Create and edit settings.py:
```
cp OpenGenomeBrowser/settings_template.py OpenGenomeBrowser/settings.py
vi OpenGenomeBrowser/settings.py
```
-   change `DEBUG` to `True` **only** for development!
-   change `GENOMIC_DATABASE` to the path to your folder structure
-   change `DATABASES[PASSWORD]` to the passwort you just set for Postgresql
-   change `ALLOWED_HOSTS` to the URL/IP you are planning to serve OpenGenomeBrowser as (example: `['opengenomebrowser.yourdomain.com']`)
-   change `SECRET_KEY` to a randomly created string; such strings can be created like this:
```python
# in a python console of a venv with django installed
from django.core.management.utils import get_random_secret_key
get_random_secret_key()
```

##### 5. populate Postgresql database
Create schemes and tables in the database
```
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
# python manage.py createsuperuser: superusername:supersafepassword
```

Import data from folder structure into database:
```
# start import (run this command again to load changes that have been made to the folder_structure into OpenGenomeBrowser)
python db_setup/import_database.py
```


##### 6. configure nginx and uwsgi (for deployment only)
If you are developing, you can run the website using `python manage.py runserver` and open [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
I recommend PyCharm Pro (free for students) as IDE as it supports Django.

Even if you want to deploy, use `python manage.py runserver` to test if that works.

Follow this tutorial: [uwsgi-docs](https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html)

Example uwsgi config:
```
[uwsgi]
chmod-socket = 664
chdir=/path/to/opengenomebrowser
home=/path/to/python/venv
module=OpenGenomeBrowser.wsgi
processes=10
threads=2
env=OpenGenomeBrowser.settings
master=True
pidfile=/tmp/opengenomebrowser-master.pid
vacuum=True
max-requests=5000
buffer-size=30000
# daemonize=/home/username/uwsgi.log
socket=/path/to/ogb.sock
```

run using `uwsgi uwsgi.ini`

Example uwsgi config:
```
upstream django {
    server unix:///path/to/ogb.sock;
}

server {
    listen       443 ssl http2 default_server;
    server_name  opengenomebrowser.yourdomain.com;
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_session_cache shared:SSL:1m;
    ssl_session_timeout  10m;
    ssl_ciphers TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE+AESGCM;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    add_header X-Frame-Options 'SAMEORIGIN' always;

    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' 'unsafe-inline' w3.org data:; style-src 'self' 'unsafe-inline'; font-src 'self'; frame-src 'self'; object-src 'self'";

    charset     utf-8;
    # max upload size
    client_max_body_size 10M;   # adjust to taste

    # Django media
    location /media  {
        alias /path/to/opengenomebrowser/dist/media;  # your Django project's media files - amend as required
    }
    
    # static files
    location /static {
        alias /path/to/opengenomebrowser/static_root; # your Django project's static files - amend as required
    }
    
    # see https://wellfire.co/learn/nginx-django-x-accel-redirects
    location /download/ {
        internal;
        alias   /path/to/database;
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        uwsgi_pass  django;
        include     /etc/nginx/uwsgi_params;
    }
}
```