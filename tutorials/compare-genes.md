<link rel="shortcut icon" type="image/svg+xml" href="favicon.svg">

# Compare genes

This page allows you to compare genes. Click 
[here](https://opengenomebrowser.bioinformatics.unibe.ch/compare-genes/?genes=FAM13496-i1-1.1_001702+FAM14217-p1-1.1_000491+FAM17891-i1-1.1_002212+FAM17927-i1-1.1_002212+FAM18356-i1-1.1_001406+FAM18815-i1-1.1_001523+FAM19038-p1-1.1_000174+FAM19471-i1-1.1_001004+FAM20558-i1-1.1_002829) 
for an example.

## Align genes

Default algorithm: `Clustal Omega` on protein sequences.

To change the algorithm (to `MAFFT` or `muscle`) or to align DNA sequences, open the settings sidebar (click on the settings wheel).

## Compare gene loci

By default, OpenGenomeBrowser loads the data for 10'000 bp around the queried genes and colorizes the genes based on orthogroup annotations.

In the resulting plot, it is possible to zoom and to pan, and to click on any gene to get more information.

This means that if two genes have the same color, they belong to the same orthogroup.

In the settings sidebar, it is possible to change the bp-range to be loaded as well as the annotation category by which to color the genes.

![compare genes demo](../media/annotation-search.apng)