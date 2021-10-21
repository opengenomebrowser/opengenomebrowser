// requires tidytree.min.js -- https://cdcgov.github.io/TidyTree/
"use strict"

/**
 * Create Phylogenetic Tree based on TaxIDs.
 *
 * genomes: list of identifiers
 * method: taxid, genome_similarity or orthofinder
 * target: div id
 * type: weighted, tree or dendrogram (see https://cdcgov.github.io/TidyTree/app/)
 * layout:
 * mode:
 */


/**
 * Create Phylogenetic Tree.
 */
function loadTree(genomes, method, target, newick_target, type, layout, mode, callback) {
    $.ajax({
        url: "/api/get-tree/",
        method: 'post',
        data: {'genomes[]': genomes, method: method},
        dataType: "json",
        success: function (data, textStatus, xhr) {
            console.log('success!!', data)

            $(newick_target).val(data.newick)

            processTreeData(data, method)

            $(target).height(600)
            $(target).empty()

            const newick = data.newick
            const species_dict = data.color_dict
            let tree = new TidyTree(
                newick ? newick : tree.data.clone(),
                {
                    parent: target,
                    layout: layout,
                    mode: mode,
                    type: type,
                    leafNodes: true,
                    branchNodes: false,
                    leafLabels: true,
                    branchLabels: true,
                    branchDistances: false,
                    ruler: false,
                    vStretch: 0.9,
                })

            if (method === 'taxid') {
                // colorize branch labels, which represent TaxIDs
                tree = tree.eachBranchLabel((label, data) => {
                    d3.select(label).style("font-size", 1 + "rem")
                        .style("text-anchor", "middle")
                        .attr("data-species-label", label.textContent)
                        .on("click", function (data) {
                            d3.event.stopPropagation()
                            showTaxidClickMenu([10, 12], data.data.id) // could use d3.event insted of null
                        })
                });
            }
            if (method === 'orthofinder') {
                // colorize branch labels, which represent TaxIDs
                tree = tree.eachBranchLabel((label, data) => {
                    d3.select(label).style("font-size", 1 + "rem")
                        .style("text-anchor", "middle")
                });
            }

            // colorize leaf labels, which represent genomes
            tree = tree.eachLeafLabel((label, data) => {
                d3.select(label).style("font-size", 1 + "rem")
                    .attr("data-species-label", species_dict[label.textContent])
                    .on("click", function (data) {
                        d3.event.stopPropagation()
                        showGenomeClickMenu([10, 12], data.data.id, species_dict[label.textContent])
                    })
            })

            turnBranchLabels(tree)

            callback(tree)
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log('jqXHR:', jqXHR)
            console.log('textStatus:', textStatus)
            console.log('errorThrown:', errorThrown)
            $(target).empty()

            processTreeData(jqXHR.responseJSON, method)

            const status = jqXHR.responseJSON?.status || ''
            const message = jqXHR.responseJSON?.message || ''

            $(target).append($('<p>', {
                class: "error-message",
                text: message
            }))

            if (jqXHR.status === 420) {
                // still calculating... Try again in 7 seconds
                $(target).append($('<div>', {
                    class: "spinner-border text-dark",
                    role: "status"
                }).append($('<span>', {class: "sr-only", text: "Loading..."})))

                setTimeout(function () {
                        loadTree(genomes, method, target, newick_target, type, layout, mode, callback)
                    }, 7000
                )
            } else {
                // failure. Abort.
                console.log('ajax-response for debugging:', jqXHR, textStatus, errorThrown)

                alert(`Failed to load ${method} tree. ${status} ${message}`)
            }

        }
    })
}


const processTreeData = function (data, method) {
    if (method === 'orthofinder') {
        if ('cache-file-path' in data && data['has-cache-file']) {
            $('#orthofinder-cached-output-download')
                .removeClass('disabled')
                .attr('href', `/files_cache/${data['cache-file-path']}`)
            $('#orthofinder-reload')
                .addClass('disabled')
                .prop("onclick", null).off("click")
        } else {
            $('#orthofinder-cached-output-download')
                .addClass('disabled')
                .attr('href', '#')
            $('#orthofinder-reload')
                .removeClass('disabled')
                .prop("onclick", null).off("click")
                .click(forceReloadOrthofinder)
        }
    }

    if ('distance-matrix' in data) {
        $('#genome-distance-matrix').data('distance-matrix', data['distance-matrix'])
    }

}

const changeTree = function (tree, property, value) {
    if (tree === undefined) {
        return  // means tree is not drawn yet
    }
    if (property === 'type') {
        tree = tree.setType(value)
    } else if (property === 'mode') {
        tree = tree.setMode(value)
    } else if (property === 'layout') {
        tree = tree.setLayout(value)
    }

    redrawTree(tree)
}

const redrawTree = function (tree) {
    tree.redraw()
    turnBranchLabels(tree)
}

const turnBranchLabels = function (tree) {
    setTimeout(function () {
        const rotation = tree.layout === 'vertical' ? 0 : -90
        tree.eachBranchLabel((label, data) => {
            d3.select(label).attr("transform", `rotate(${rotation})`)
        })
    }, 1000)
}

const addTreeSizeListener = function (tree, divId) {
    const div = document.getElementById(divId)

    const resizefunction = function () {
        clearTimeout(ajax_timer)
        ajax_timer = setTimeout(function () {
            redrawTree(tree)
        }, 500)
    }

    if (div.hasOwnProperty('__resizeListeners__')) {
        div.__resizeListeners__.length = 0  // remove all listeners
        div.__resizeListeners__.push(resizefunction)
    } else {
        addResizeListener(div, resizefunction)
    }
}