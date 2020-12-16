## Annotation descriptions (optional)

To tell OpenGenomeBrowser and its users what thinks like `K01695`, `EC:4.2.1.20` and `GO:0005829` mean, 
create a file for each annotation type that maps the identifier to a short description.


Available types:
* `KG`: (KEGG gene)
* `KR`: (KEGG reaction)
* `GO`: (Gene ontology)
* `EC`: (Enzyme commission)
* `CU`: (Custom)


```
├── organisms
    └── ...
└── annotation-descriptions
     ├── EC.tsv
     └── ...
```


This is the format:


```
EC:4.2.1.17\tbeta-hydroxyacyl-CoA dehydrase
EC:4.2.1.18\tmethylglutaconyl-CoA hydratase
EC:4.2.1.19\timidazoleglycerol-phosphate dehydratase
EC:4.2.1.20\tL-tryptophan synthetase
```


### Import annotation descriptions

This step is only required if these files were added after the genomes were imported.

1.  [Open a terminal in the container](https://github.com/opengenomebrowser/opengenomebrowser-docker-template#open-a-terminal-in-the-container)
1.  run `python db_setup/manage_ogb.py import-annotation-descriptions`
