<link rel="shortcut icon" type="image/svg+xml" href="/opengenomebrowser/favicon.svg">

# Phylogenetic Trees

In the [genomes table](https://opengenomebrowser.bioinformatics.unibe.ch/genomes), select multiple genomes (using `Shift` and `Ctrl`) and 
open the context menu using right click. Then, click on "Show phylogenetic trees".

The following analysis options are available:

  - TaxId-based tree: Short calculation time but based on taxid-annotations only (NOT on sequence similarity).
  - Genome-similarity-based tree: Short calculation time, based on sequence similarity of pairwise comparisons of assemblies (default: GenDisCal - PaSiT6 ([Goussarov et al., Bioinformatics, 2020](https://pubmed.ncbi.nlm.nih.gov/31899493/))
  - Single-copy-ortholog-based tree: Long calculation time but the result is of higher quality (i.e. more reliable) than the former options. The methodology is based on [OrthoFinder](https://github.com/davidemms/OrthoFinder) consensus tree of all single-copy ortholog alignments ([Emms et al., Molecular Biology and Evolution, 2017]())

![trees demo](../media/trees.apng )
