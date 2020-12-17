## Log in

A demo instance of OpenGenomeBrowser is hosted here: [opengenomebrowser.bioinformatics.unibe.ch](https://opengenomebrowser.bioinformatics.unibe.ch/).

It contains 24 genomes published in the paper [Roder et al., Microorganisms, 2020](https://www.mdpi.com/2076-2607/8/7/966).

Click on the logo to proceed to the login screen. Log in with username `test` and password `testtesttest`.

## Genomes table

First, let's explore the genomes table. Click on "[Genomes](https://opengenomebrowser.bioinformatics.unibe.ch/genomes)".

This page contains powerful filter and search options.
  - Columns can be sorted and filtered by clicking on the column header.

To dive deeper into a genome, open the context menu: **right click** on a row.
  - This is an exception: elsewhere on OpenGenomeBrowser, a normal **left click** opens the context menu.

It is possible to select **multiple** genomes by holding down `Shift` and/or `Ctrl`, then clicking on rows.
  - The context menu (right click!) will look different and have more options if multiple genomes are selected.

The settings sidebar can be opened by clicking on the settings wheel. It provides the following options:
  - The table, in the current view, can be downloaded in CSV or Excel format.
  - By default, only `representative` genomes are shown. This can be changed in the settings sidebar.
  - Genomes that are marked `restricted` or `contaminated` are hidden by default. This can be changed in the settings sidebar.
  - Additional metadata columns may be added by moving a field from "available columns" to "visible columns". To submit the changes, click on "Update table".

![pathways demo](media/genomes.apng)

## Single genome view

In the [genomes table](https://opengenomebrowser.bioinformatics.unibe.ch/genomes), right click on a row and select "[Open genome info](https://opengenomebrowser.bioinformatics.unibe.ch/genome/FAM18356-i1-1.1/)".
  - This page contains all metadata that was fed into OpenGenomeBrowser.
  - Links to download the associated files are at the bottom of the page.

## 

![pathways demo](media/pathways.apng)

## Phylogenetic Trees

In the [genomes table](https://opengenomebrowser.bioinformatics.unibe.ch/genomes), select multiple genomes (using `Shift` and `Ctrl`) and 
open the context menu using right click. Then, click on "Show phylogenetic trees".

It has the following options:

  - TaxId-based tree: Fastest, based on taxid-annotations only.
  - Genome-similarity-based tree: Still fast, based on pairwise assembly similarity (default: GenDisCal - PaSiT6 ([Goussarov et al., Bioinformatics, 2020](https://pubmed.ncbi.nlm.nih.gov/31899493/))
  - Single-copy-ortholog-based tree: Slow, high quality tree, based on [OrthoFinder](https://github.com/davidemms/OrthoFinder) consensus tree of all single-copy ortholog alignments ([Emms et al., Molecular Biology and Evolution, 2017]())

![pathways demo](media/trees.apng )

## Blast

![pathways demo](media/blast.apng)

## Annotation search

![pathways demo](media/annotation-search.apng)

## Gene trait matching

![pathways demo](media/gene-trait-matching.apng)

## Magic strings

![pathways demo](media/magic-strings.apng)
