"use strict";

/**
 * Load dna-feature-viewer svg for specific gene.
 */
function load_dna_feature_viewer_single(gene_identifier, target_div) {
    console.log('gene_identifier  :', gene_identifier);

    $.getJSON('/api/dna-feature-viewer-single/', {'gene_identifier': gene_identifier}, function (data) {

        target_div.append(data['plot_div']);
        eval(data['script'])
    });
}

/**
 * Load dna-feature-viewer svg for multiple genes.
 */
function load_dna_feature_viewer_multi(gene_identifiers, target_div) {
    console.log('gene_identifiers  :', gene_identifiers);

    $.getJSON('/api/dna-feature-viewer-multi/', {'gene_identifiers': gene_identifiers}, function (data) {
        target_div.append(data['plot_div'])
        eval(data['script'])
    }).done(function () {
        // hide spinner
        $('#gene-loci-spinner').hide()

        // make loci sortable
        new Sortable(document.getElementById('gene-loci'), {
            handle: '.handle',
            animation: 150
        })

        // enable click menu
        $('.ogb-tag.gene').click(function (event) {
            showGeneClickMenu(event) // , 'auto', '#gene-loci')
        })
        $('.ogb-tag.taxid').click(function (event) {
            showTaxidClickMenu(event)
        })
    });
}

function geneLabelClicked(label) {
    showGeneClickMenu([50, 50], label);
}