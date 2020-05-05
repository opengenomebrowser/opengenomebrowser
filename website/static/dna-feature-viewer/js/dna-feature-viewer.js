"use strict";

/**
 * Load dna-feature-viewer svg for specific gene.
 */
function load_dna_feature_viewer(gene_identifier, target_div) {
    console.log('gene_identifier  :', gene_identifier);

    $.getJSON('/api/dna-feature-viewer/', {'gene_identifier': gene_identifier}, function (data) {

        $('#gene-locus').html(data['plot_div']);
        eval(data['script'])
    });
}

function geneLabelClicked(label) {
    ShowGeneContextMenu([50,50], label);
}