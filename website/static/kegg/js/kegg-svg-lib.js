"use strict";

const annotation_types = ['k', 'ec', 'c', 'map', 'r', 'g', 'd', 'dg'];
const annotation_types_info = {
    'k': {'href': 'https://www.genome.jp/dbget-bin/www_bget?'},
    'ec': {'href': 'https://www.genome.jp/dbget-bin/www_bget?'},
    'c': {'href': 'https://www.genome.jp/dbget-bin/www_bget?'},
    'map': {'href': 'https://www.genome.jp/kegg-bin/show_pathway?'},
    'r': {'href': 'https://www.genome.jp/dbget-bin/www_bget?'},
    'g': {'href': 'https://www.genome.jp/dbget-bin/www_bget?'},
    'd': {'href': 'https://www.genome.jp/dbget-bin/www_bget?'},
    'dg': {'href': 'https://www.genome.jp/dbget-bin/www_bget?'}
};
const default_kegg_svg_id = 'kegg-svg';

function highlightKeggMap({
                              kegg_svg_id = default_kegg_svg_id, color = "red",
                              annotations_to_highlight = {}  // e.g. {k: ['K00014']}
                          }) {
    clearMap(kegg_svg_id);
    // check input
    assert(kegg_svg_id.constructor === String && document.getElementById(kegg_svg_id) != null, "error in highlightKeggMap: could not find element with kegg_svg_id");
    assert(color.constructor === String, "error in highlightKeggMap: color must be string");

    let kegg_map = document.getElementById(kegg_svg_id); // $('#kegg_map');
    let shapes = kegg_map.querySelector('[name="shapes"]');

    let all_shapes = shapes.querySelectorAll("a");
    for (let i = 0; i < all_shapes.length; i++) {
        let shape = all_shapes[i];

        if (doesStrainCoverShape(annotations_to_highlight, shape)[0]) {
            shape.firstElementChild.setAttribute('fill', color);
        }
    }
}

function clearMap(kegg_svg_id = default_kegg_svg_id) {
    assert(kegg_svg_id.constructor === String && document.getElementById(kegg_svg_id) != null, "error in clearMap: could not find element with kegg_svg_id");
    let kegg_map = document.getElementById(kegg_svg_id); // $('#kegg_map');
    let shapes = kegg_map.querySelector('[name="shapes"]');
    let all_shapes = shapes.querySelectorAll("a");
    for (let i = 0; i < all_shapes.length; i++) {
        all_shapes[i].firstElementChild.setAttribute('fill', 'transparent');
        all_shapes[i].removeAttribute('data-strains-have');
        all_shapes[i].removeAttribute('data-strains-lack');
        all_shapes[i].removeAttribute('data-annos-to-strains');
    }
}

function doesStrainCoverShape(strain_annos, shape) {
    let strain_annotations = Object.keys(strain_annos); // e.g. [ "k", "ec" ]

    for (let anno in strain_annotations) {
        assert(annotation_types.includes(strain_annotations[anno]),
            "error in doesStrainCoverShape: unknown annotation type: " + strain_annotations[anno])
    }

    // this is returned if the strain does not cover anything
    let strain_covers_shape = false;
    let annotations_to_strains = [];
    let all_shared = [];

    for (let i in strain_annotations) {
        let shape_annos = shape.getAttribute('data-' + strain_annotations[i]).split(',');
        let annos = strain_annos[strain_annotations[i]];
        if (shape_annos[0] !== "") {
            let shared = intersection(shape_annos, annos);

            // for (let i in shared) {
            //     annotations_to_strains.push({
            //         key: shared[i],
            //         value: strain_name
            //     });
            // }

            if (shared.length > 0) {
                strain_covers_shape = true;
                all_shared = all_shared.concat(shared)
            }
        }
    }
    return [strain_covers_shape, all_shared]
}

function gradientKeggMap({
                             kegg_svg_id = default_kegg_svg_id, colors = ['yellow', 'red'], strains = {}
                         }) {
    clearMap(kegg_svg_id);

    let strain_names = Object.keys(strains);
    let color_array = chroma.scale(colors).mode('lch').colors(strain_names.length);

    // get elements in svg
    let kegg_map = document.getElementById(kegg_svg_id); // $('#kegg_map');
    let shapes = kegg_map.querySelector('[name="shapes"]');

    let all_shapes = shapes.querySelectorAll("a");
    for (let i = 0; i < all_shapes.length; i++) {
        let shape = all_shapes[i];
        let strains_have = [];
        let strains_lack = [];
        let annos_to_strains = {};

        let shape_annos = shape.getAttribute('data-all-annotations').split(',')
        for (let i in shape_annos) {
            annos_to_strains[shape_annos[i]] = []
        }

        for (let strain in strains) {
            let dscs = doesStrainCoverShape(strains[strain], shape);  // returns [strain_covers_shape, strain_to_annotations]
            if (dscs[0]) {
                strains_have.push(strain);

                for (let i in dscs[1]) {
                    annos_to_strains[dscs[1][i]].push(strain);
                }

            } else {
                strains_lack.push(strain);
            }
        }

        // color shape
        if (strains_have.length > 0) {
            shape.firstElementChild.setAttribute('fill', color_array[strains_have.length - 1]);
        }

        // set attributes to later create context menus
        shape.setAttribute('data-strains-have', strains_have);
        shape.setAttribute('data-strains-lack', strains_lack);
        shape.setAttribute('data-annos-to-strains', JSON.stringify(annos_to_strains));
    }
}

function manualKeggMap({
                           kegg_svg_id = default_kegg_svg_id, dictionary
                       }) {
    clearMap(kegg_svg_id);
    let keys = Object.keys(dictionary);
    let annotations_to_highlight = {};
    for (let key in keys) {
        key = keys[key];
        let annotations = [];
        for (let anno_color_pair in dictionary[key]) {
            annotations.push(dictionary[key][anno_color_pair][0]);
        }
        annotations_to_highlight[key] = annotations
    }

    // get elements in svg
    let kegg_map = document.getElementById(kegg_svg_id); // $('#kegg_map');
    let shapes = kegg_map.querySelector('[name="shapes"]');

    let all_shapes = shapes.querySelectorAll("a");
    for (let i = 0; i < all_shapes.length; i++) {
        let shape = all_shapes[i];
        if (doesStrainCoverShape(annotations_to_highlight, shape)[0]) {
            let color = getManualColor(annotations_to_highlight, dictionary, shape);
            shape.firstElementChild.setAttribute('fill', color);
        }
    }
}

function getManualColor(annotations_to_highlight, dictionary, shape) {
    let strain_annotations = Object.keys(annotations_to_highlight); // e.g. [ "k", "ec" ]
    let colors = [];
    for (let i in strain_annotations) {
        let shape_annos = shape.getAttribute('data-' + strain_annotations[i]).split(',');
        let strain_annos = annotations_to_highlight[strain_annotations[i]];
        let strain_annos_to_color = dictionary[strain_annotations[i]];

        if (shape_annos[0] !== "" && doIntersect(shape_annos, strain_annos)) {
            let shared = shape_annos.filter(value => strain_annos.includes(value));
            for (let i in shared) {
                let match_idx = strain_annos.indexOf(shared[i]);
                assert(strain_annos_to_color[match_idx][0] == shared[i]);
                colors.push(strain_annos_to_color[match_idx][1])
            }
        }
    }
    assert(colors.length != 0,
        "Error: the function getManualColor must be used only if there is an intersection!");
    assert(colors.length == 1,
        "Error: more than one color was specified for this shape!", shape);

    return colors[0]
}

function saveDivAsPng(element_id) {
    html2canvas(document.querySelector("#" + element_id)).then(function (canvas) {
        saveUriAs(canvas.toDataURL(), 'custom-kegg.png');
    });
}

function saveUriAs(uri, filename) {
    var link = document.createElement('a');
    if (typeof link.download === 'string') {
        link.href = uri;
        link.download = filename;
        //Firefox requires the link to be in the body
        document.body.appendChild(link);
        //simulate click
        link.click();
        //remove the link when done
        document.body.removeChild(link);
    } else {
        window.open(uri);
    }
}


function assert(condition, message) {
    if (!condition) {
        message = message || "Assertion failed";
        if (typeof Error !== "undefined") {
            throw new Error(message);
        }
        throw message; // Fallback
    }
}

function doIntersect(a, b) {
    return intersection(a, b).length > 0;
}

function intersection(a, b) {
    var t;
    if (b.length > a.length) t = b, b = a, a = t; // indexOf to loop over shorter
    return a.filter(function (e) {
        return b.indexOf(e) > -1;
    });
}

function isDescendant(parent, child) {
    return child.parent('#' + parent.attr('id')).length > 0;
}