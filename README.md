# OpenGenomeBrowser

**ALERT: This software is still under development! If you want to try it out, contact the developer first!**

**Prototype:** [opengenomebrowser.bioinformatics.unibe.ch](https://opengenomebrowser.bioinformatics.unibe.ch/)

To talk to the developer informally, join the OpenGenomeBrowser [Discord channel](https://discord.gg/mDm4fqf).
<hr>

_OpenGenomeBrowser is a portable and scalable web platform for comparative genomics._

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
└── annotation-descriptions  # optional
     ├── OL.tsv
     └── ...
└── OrthoFinder  # optional
     └── fastas
         ├── fasta1.faa
         ├── ...
         └── OrthoFinder
            └── ...
└── orthologs  # optional
     └── orthologs.tsv
└── pathway_maps  # optional
     ├── type_dictionary.json
     └── svg
         ├── map1.svg
         └── ...
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
    "library_preparation": null,
    "sequencing_tech": null,
    "sequencing_tech_version": null,
    "sequencing_date": null,
    "sequencing_coverage": null,
    "read_length": null,
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

1.   prerequisites: docker and docker-compose
1.   todo

### Example: get OpenGenomeBrowser with test-database running:

