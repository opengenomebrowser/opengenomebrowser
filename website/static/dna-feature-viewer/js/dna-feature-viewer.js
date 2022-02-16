"use strict"

/**
 * Load dna-feature-viewer svg for specific gene.
 */
async function load_dna_feature_viewer_single(gene_identifier, target_div, span = 30000) {
    console.log('gene_identifier  :', gene_identifier, span)

    await $.post('/api/dna-feature-viewer-single/', {
        'gene_identifier': gene_identifier,
        'span': span
    }, function (data) {
        target_div.append(data['plot_div'])
        eval(data['script'])
    }, "json")
        .fail(function (data, textStatus, jqXHR) {
            if (data?.status === 409) {
                console.log('Error 409 info:', data, textStatus, jqXHR)
                alertModal('info', 'Info', data?.responseJSON?.message)
            } else {
                console.log('fail', data, textStatus, jqXHR)
                alertModal('danger', 'Error', data?.responseJSON?.message || `(no message) ${data?.status} ${data?.statusText}`)
            }
        })
}

/**
 * Load dna-feature-viewer svg for multiple genes.
 */
async function load_dna_feature_viewer_multi(gene_identifiers, target_div, span = 10000, colorize_by = '--') {
    console.log('gene_identifiers  :', gene_identifiers, 'span', span, 'colorize_by', colorize_by)


    await $.post('/api/dna-feature-viewer-multi/', {
        'gene_identifiers': gene_identifiers,
        'span': span,
        'colorize_by': colorize_by
    }, function (data) {
        target_div.append(data['plot_div'])
        eval(data['script'])
    }, "json")
        .done(function () {
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
        })
        .fail(function (data, textStatus, jqXHR) {
            if (data?.status === 409) {
                console.log('Error 409 info:', data, textStatus, jqXHR)
                alertModal('info', 'Info', data?.responseJSON?.message)
            } else {
                console.log('fail', data, textStatus, jqXHR)
                alertModal('danger', 'Error', data?.responseJSON?.message || `(no message) ${data?.status} ${data?.statusText}`)
            }
        })
}

function geneLabelClicked(label) {
    showGeneClickMenu([50, 50], label)
}