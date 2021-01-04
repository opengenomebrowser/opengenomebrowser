<link rel="shortcut icon" type="image/svg+xml" href="/opengenomebrowser/favicon.svg">

# Set-up

OpenGenomeBrowser is very easy to install as a docker container. Follow [this tutorial](https://github.com/opengenomebrowser/opengenomebrowser-docker-template/) to get it running with the demo database!

In order to run OpenGenomeBrowser with your own data, you will have to prepare your files as described below.




## Folder structure

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

### Notes:

-   genome names must start with the name of the corresponding organism
    -   we _suggest_ to use this suffix format:
        `organism`-`isolate`-`assembly`.`annotation`
    -   example: organism=`EXAMPLE1234` -> `EXAMPLE1234-2-1.1`
-   gene locus tags must start with the genome identifier, then an underline (`_`)
    -   example: `EXAMPLE1234-2-1.1_000001`




## Metadata (NOTE: these specifications are not final!)

#### Notes:

*   paths are relative to the genome folder, i.e. it's fine to have files in a subfolders of the genome folder
*   date format: `"%Y-%m-%d"`, i.e. `2000-12-31`

##### organism.json:

(all mandatory fields have dummy data, all non-mandatory fields have null-input)

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

(all mandatory fields have dummy data, all non-mandatory fields have null-placeholder-input)

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

```json
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

Allowed types:
* `KG`: (KEGG gene, format: `K000000`)
* `KR`: (KEGG reaction, format: `R00000`)
* `GO`: (Gene ontology, format: `GO:0000000`)
* `EC`: (Enzyme commission, format: `EC:0.0`, `EC:0.0.0` or `EC:0.0.0.0`)
* `CU`: (Custom)

```
"custom_annotations": [
        {
            "date": "0000-00-00",
            "file": "annotations.ko",
            "type": "KG"
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



## Additional options

- [Annotation descriptions](/installation/annotation-descriptions.md)
- [Orthologs and Orthofinder](/installation/orthologs.md)
- [Pathway maps](/installation/pathway-maps.md)


