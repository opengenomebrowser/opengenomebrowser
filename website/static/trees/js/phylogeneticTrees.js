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

            if ('distance-matrix' in data) {
                $('#genome-distance-matrix').data('distance-matrix', data['distance-matrix'])
            }

            $(target).empty()
            $(target).height(600)

            const newick = data.newick
            const species_dict = data.color_dict

            let settings = {
                //whether the tree visualisation takes into account tree branch lengths
                useLengths: true,
                //size of font on node labels
                fontSize: 14,
                //thickness of branch lines
                lineThickness: 3,
                //size of tree nodes
                nodeSize: 3,
                //multiplier for treeWidth (not width in px)
                treeWidth: 500,
                //multiplier for height of a leaf (not height of whole tree)
                treeHeight: 15,
                //whether compared tree moves to best corresponding node when node in other tree highlighted
                moveOnClick: true,
                //whether zoom slider overlay is enabled
                enableZoomSliders: true,
                //minimum zoom level
                scaleMin: 0.05,
                //maximum zoom level
                scaleMax: 5,
                //color of the text for the length scale
                scaleColor: "black",
                //function to call when a long operation is occuring
                loadingCallback: function () {
                },
                //function to call when a long operation is complete
                loadedCallback: function () {
                },
                //text for internal nodes
                internalLabels: "name", //none, name, length, similarity
                //whether the link to download the tree as an SVG is shown
                enableDownloadButtons: true,
                //whether zoom on mouseover is enabled
                enableFisheyeZoom: false,
                //zoom mode for scaling the visualisation
                zoomMode: "traditional", //semantic, traditional
                //whether the tree is scaled to fit in the render space on initial render
                fitTree: "scale", //none, scale
                //whether size control overlay is enabled
                enableSizeControls: true,
                //whether search overlay is enabled
                enableSearch: true,
                //depth to which nodes are automatically collapsed e.g 3 collapses all nodes deeper than depth 3
                autoCollapse: null, // 0,1,2,3... etc
                //enable reroot functionality to find best root based on opposite tree in compare mode
                enableRerootFixedButtons: true,
                //swaps bipartitions until best resembles to opposite tree is found
                enableSwapFixedButtons: true,
                //enables to share tree as gist
                enableCloudShare: false,
                //enables buttons to ladderize trees
                enableLadderizeTreeButton: true,
                //enables all opposite tree actiosn
                enableOppositeTreeActions: true,
                //allows to align tiplabels
                alignTipLables: false,
                //allows to search for multiple leaves
                selectMultipleSearch: false,
            }

            console.log('method', method)
            if (method === 'taxid') {
            } else if (method === 'orthofinder') {
            } else if (method === 'genome-similarity') {
            }

            console.log(newick)

            let treecomp = TreeCompare().init(settings)

            let tree = treecomp.addTree(
                newick,
                undefined,
                "single"
            )

            console.log('tree1', tree)

            treecomp.viewTree(tree.name, target.substring(1), 'vis-container-2')


            console.log('DONE', tree)


            // callback(tree)
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log('jqXHR:', jqXHR)
            console.log('textStatus:', textStatus)
            console.log('errorThrown:', errorThrown)
            $(target).empty()

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