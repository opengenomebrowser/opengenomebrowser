<link rel="shortcut icon" type="image/svg+xml" href="/opengenomebrowser/favicon.svg">

## Welcome to OpenGenomeBrowser 
 
**Demo instance:** [opengenomebrowser.bioinformatics.unibe.ch](https://opengenomebrowser.bioinformatics.unibe.ch/)

<hr>

_OpenGenomeBrowser is a dynamic and scalable web platform for comparative genomics._

  - OpenGenomeBrowser enables users to:
    - Filter and search large genomic datasets using metadata
    - Generate of dendrograms (Taxid-based, ANI-based and OrthoFinder-based)
    - Search for annotations in genomes
    - Visualize genomes on pathway maps
    - Visualize gene loci
    - Perform BLAST searches (nucleotide or protein level)
    - Download raw data through a webbrowser 
  - OpenGenomeBrowser has only few prerequisites:
    - Assembly and genome annotation files must be stored in a defined folder structure
    - At least one metadata file for each genome and organism is required
  - OpenGenomeBrowser is flexible:
    - [OrthoFinder](https://github.com/davidemms/OrthoFinder) is recommended, but not required (allows core genome dendrogram calculations)
    - Computationally intensive processes can be outsourced to a cluster

<div align="center">
<img src="https://raw.githubusercontent.com/opengenomebrowser/opengenomebrowser/master/website/static/global/customicons/ogb-full.svg"  width="500px">
</div>


### Key concepts

  - _Organism_: biological entity, e.g. a microbial strain. 
  - _Genome_: one sample of a particular organism. An organism can comprise more than one genome, e.g. if a particular strain has been sequenced multiple times   
  - _Representative_: the 'gold standard' genome of an organism


## Tutorial

Play around with the demo instance of [OpenGenomeBrowser](opengenomebrowser.bioinformatics.unibe.ch/) and read the [tutorial](/tutorial.md)!


## Installation

Click [here](/installation.md) to read the instructions.


## Get help

If you find a bug that has not been reported yet, [submit an issuehere on GitHub](https://github.com/opengenomebrowser/opengenomebrowser/issues).

To chat with the developer, join the OpenGenomeBrowser [Discord channel](https://discord.gg/mDm4fqf).
