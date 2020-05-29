// requires tidytree.min.js -- https://cdcgov.github.io/TidyTree/
"use strict"

/**
 * Create Phylogenetic Tree based on TaxIDs.
 *
 * members: list of identifiers
 * method: taxid, ani or orthofinder
 * target: div id
 * type: weighted, tree or dendrogram (see https://cdcgov.github.io/TidyTree/app/)
 * layout:
 * mode:
 */


/**
 * Create Phylogenetic Tree based on ANI similarity.
 */
let loadTree = async function (members, method, target, newick_target, type, layout, mode) {
    // load newick synchronously
    let go_on

    let load_tree = function () {
        // abort if current_members have changed
        if (members.join('::') != current_members.join('::')) {
            go_on = false
            return null
        }


        let ajax = $.ajax({
            url: "/api/get-tree",
            data: {'members[]': members, method: method},
            async: false,
            dataType: "json",
        })

        if (ajax.status === 409) {
            // still calculating...
            console.log('still calculating', ajax.responseJSON.message, ajax)
            go_on = true

            $(target).empty()
            $(target).append($('<p>', {
                class: "error-message",
                text: ajax.responseJSON.message
            }))
            $(target).append($('<div>', {
                class: "spinner-border text-dark",
                role: "status"
            }).append($('<span>', {class: "sr-only", text: "Loading..."})))

            return null
        }

        if (ajax.status !== 200) {
            alert(`Failed to load ${method} tree.`)
            console.log('ajax-response for debugging:', ajax)
            go_on = false
            return null
        }

        $(newick_target).val(ajax.responseJSON.newick)

        $(target).height(600)
        $(target).empty()
        go_on = false

        const newick = ajax.responseJSON.newick
        const species_dict = ajax.responseJSON.color_dict
        tree = new TidyTree(
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
                        ShowTaxidContextMenu([10, 12], data.data.id) // could use d3.event insted of null
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

        // colorize leaf labels, which represent Members
        tree = tree.eachLeafLabel((label, data) => {
            d3.select(label).style("font-size", 1 + "rem")
                .attr("data-species-label", species_dict[label.textContent])
                .on("click", function (data) {
                    d3.event.stopPropagation()
                    ShowMemberContextMenu([10, 12], data.data.id, []) // could use d3.event insted of null
                })
        });

        return tree
    }

    let tree
    do {
        tree = await load_tree()

        if (go_on) {
            await sleep(5000)  // sleep from base.js
        } else {
            await sleep(500)
        }

    } while (go_on)

    turnBranchLabels(tree)

    return tree
}

let turnBranchLabels = async function (tree) {
    console.log('turn branch labels')
    console.log(tree)
    if (tree == null) {
        return
    }

    tree = await tree.redraw()

    if (tree.layout === 'vertical' || tree.layout === 'horizontal') {
        let rotation
        if (tree.layout === 'vertical') {
            rotation = 0
        } else {
            rotation = -90
        }
        await sleep(1000) // i hate javascript so much
        tree = tree.eachBranchLabel((label, data) => {
            d3.select(label).attr("transform", `rotate(${rotation})`)
        })
    }
}

let redrawTree = function (tree_promise) {
    tree_promise.then(function (tree) {
        turnBranchLabels(tree)
    })
}

let changeTree = function (tree_promise, property, value) {
    tree_promise.then(function (tree) {
        console.log(tree, property)
        if (property === 'type') {
            tree = tree.setType(value)
        } else if (property === 'mode') {
            tree = tree.setMode(value)
        } else if (property === 'layout') {
            tree = tree.setLayout(value)
        }

        redrawTree(tree_promise)
    })
}