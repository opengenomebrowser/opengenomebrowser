## Orthologs (optional)

Ortholog annotations are handled differently than regular annotations. The reason is that ortholog information for all genomes (result of orthofinder) is stored in one file which links orthologs to individual genes (`orthologs/orthologs.tsv`):

```
N0.HOG0000000\tgenome_1_123, genome_2_234
N0.HOG0000001\tgenome_2_345, genome_3_456, genome_4_567
N0.HOG0000002\tgenome_6_789, genome_7_890
```

Descriptions to orthologs may be provided in an additional file (`annotation-descriptions/OL.tsv`) with the following format:

```
N0.HOG0000000\tamino acid ABC transporter ATP-binding protein
N0.HOG0000001\twinged helix-turn-helix transcriptional regulator
N0.HOG0000002\tDNA topoisomerase (ATP-hydrolyzing) subunit B
```

### Import orthologs

1. [Open a terminal in the container](https://github.com/opengenomebrowser/opengenomebrowser-docker-template#open-a-terminal-in-the-container)
1. run `python db_setup/manage_ogb.py import-orthologs`

## OrthoFinder (recommended, but optional)

If you want to use [OrthoFinder](https://github.com/davidemms/OrthoFinder), set the `ORTHOFINDER_ENABLED` environment variable to `true` (
see [`template.env`](https://github.com/opengenomebrowser/opengenomebrowser-docker-template/blob/main/production-template.env)).

OpenGenomeBrowser uses OrthoFinder to calculate core genome dendrograms. To shorten computation time and effort, OpenGenomeBrowser expects that the
pairwise DIAMOND searches have already been run for all genomes for which this functionality should be available.

If you choose to add OrthoFinder, do as follows (can be done automatically using `db_setup/init_orthofinder.py`):

```
├── organisms
    └── ...
└── OrthoFinder
     └── fastas
         ├── <genome-identifier>.faa -> ../../organisms/.../genomes/<genome-identifier>/protein.faa
         ├── <genome-identifier>.faa -> ../../organisms/.../genomes/<genome-identifier>/protein.faa
         └── ...
```

1. Link (or copy) all protein fastas to `OrthoFinder/fastas`
    1. If your database is very big, you could exclude non-representative and contaminated genomes, for example 1.The fastas **must** be named as
       follows: `<genome-identifier>.<suffix>`
    1. Tell OpenGenomeBrowser what your suffix is (
       see [`template.env`](https://github.com/opengenomebrowser/opengenomebrowser-docker-template/blob/main/production-template.env))
1. Run OrthoFinder (`orthofinder -f /path/to/OrthoFinder/fastas`)
    1. Because previously performed pairwise comparisons are stored and can be re-used OrthoFinder analyses can be updated very efficiently by simply adding or removing protein files.
       See [OrthoFinder docs](https://github.com/davidemms/OrthoFinder#advanced-usage) for more information.

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
