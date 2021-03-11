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
        success: function (data) {
            console.log('success!!', data)

            $(newick_target).val(data.newick)

            if ('distance-matrix' in data) {
                $('#genome-distance-matrix').data('distance-matrix', data['distance-matrix'])
            }

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

            console.log('DONE', tree)

            turnBranchLabels(tree)

            callback(tree)
        },
        error: function (data) {
            $(target).empty()

            const status = 'responseJSON' in data && 'status' in data.responseJSON ? data.responseJSON.status : ''
            const message = 'responseJSON' in data && 'message' in data.responseJSON ? data.responseJSON.message : ''

            $(target).append($('<p>', {
                class: "error-message",
                text: message
            }))

            if (data.status === 408) {
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
                console.log('ajax-response for debugging:', data)

                alert(`Failed to load ${method} tree. ${status} ${message}`)
            }

        }
    })
}


let changeTree = function (tree, property, value) {
    if (tree === undefined) {
        return  // means tree is not drawn yet
    }
    console.log(tree, property)
    if (property === 'type') {
        tree = tree.setType(value)
    } else if (property === 'mode') {
        tree = tree.setMode(value)
    } else if (property === 'layout') {
        tree = tree.setLayout(value)
    }

    redrawTree(tree)
}

let redrawTree = function (tree) {
    tree.redraw()
    turnBranchLabels(tree)
}

let turnBranchLabels = function (tree) {
    console.log('turn branch labels')
    setTimeout(function () {
        const rotation = tree.layout === 'vertical' ? 0 : -90
        tree.eachBranchLabel((label, data) => {
            d3.select(label).attr("transform", `rotate(${rotation})`)
        })
    }, 1000)
}

let addTreeSizeListener = function (tree, divId) {
    addResizeListener(document.getElementById(divId), function () {
        clearTimeout(ajax_timer)
        ajax_timer = setTimeout(function () {
            console.log('resizing')
            redrawTree(tree)
        }, 500)
    })
}