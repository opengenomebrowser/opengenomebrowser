"use strict"

/**
 * Remove metadata tags from shapes
 *
 * From each shape, remove:
 *   - data-strains
 *   - data-manual-number
 *   - from each annotation in data-annotations:
 *      - 'strains'
 *      - 'manual-number
 */
function resetMap() {
    $(".shape").each(function () {
        // make fill transparent
        this.firstElementChild.setAttribute('fill', 'transparent')
        // empty strains from shape
        $(this).removeData('strains')
        $(this).removeData('manual-number')
        // empty strains from annotations
        let annotations = $(this).data('annotations')
        annotations.forEach(function (annotation, index) {
            delete annotations[index]['strains']
            delete annotations[index]['manual-number']
        })
        $(this).data('annotations', annotations)
    })
}

/**
 * Colorize shapes by whether they cover certain annotations
 *
 * @param  {string} color The color for covered shapes
 * @param  {Array}  annotations_to_highlight Array of annotations to highlight
 */
function highlightBinary(
    color = "red",
    annotations_to_highlight = []  // e.g. ['K00001']
) {
    resetMap()

    $(".shape").each(function (index) {
        let annotations = $(this).data('annotations')
        if (getCoveredAnnotations(annotations_to_highlight, annotations).length) {
            this.firstElementChild.setAttribute('fill', color)
        } else {
            this.firstElementChild.setAttribute('fill', 'transparent')
        }
    })
}

/**
 * Colorize shapes by how many strains have their annotations
 *
 * @param  {Array}  colors Two colors: The first for shapes that are covered by one annotation,
 *   the second for shapes that are covered by all annotations
 * @param  {Object} strains A dictionary { strain => [ annotation ]}
 *   Example: { Strain1: [ "R09127", "R01788", … ], Strain2: [ … ], … }
 *
 * Adds...
 *   - 'data-strains' to shape, for example:
 *        { covering: [ "Strain1", … ], not-covering: [] }
 *   - 'strains' to annotations in 'data-annotations':
 *        { name: "K01223", …, strains: [ "Strain1", … ] }
 * This data can be removed using resetMap()
 */
function highlightStrains(
    strains,
    colors = ['yellow', 'red']
) {
    resetMap()

    let strain_names = Object.keys(strains)
    let color_array = chroma.scale(colors).mode('lch').colors(strain_names.length)

    function gradientShape(shape) {
        let annotations = $(shape).data('annotations')
        let covering_strains = new Set()
        let not_covering_strains = new Set()
        annotations.forEach(function (annotation, index) {
            annotations[index]['strains'] = new Set()
        })

        // for each strain, see if it covers anything
        $.each(strains, function (s_name, s_annotations) {
            let covering = false
            annotations.forEach(function (annotation, index) {
                if (s_annotations.includes(annotation['name'])) {
                    annotations[index]['strains'].add(s_name)
                    covering_strains.add(s_name)
                    covering = true
                }
            })
            if (!covering) {
                not_covering_strains.add(s_name)
            }

        })

        // write info back to shape
        $(shape).data('strains', {"covering": covering_strains, "not-covering": not_covering_strains})
        $(shape).data('annotations', annotations)

        // color shape
        const n_covered = covering_strains.size
        if (n_covered > 0) {
            shape.firstElementChild.setAttribute('fill', color_array[n_covered - 1])
        }
    }

    $(".shape").each(function (index) {
        gradientShape(this)
    })
}

/**
 * Colorize shapes by continuous numbers between 0 and 1
 *
 * @param  {Array}  colors Two colors: The first for shapes that are covered by one annotation,
 *   the second for shapes that are covered by all annotations
 * @param  {Object} annotation_to_number A dictionary { annotation => number }
 *   Example: { C00033: 0.24, C00031: 0.53, … }
 *
 * Adds...
 *   - 'data-manual-number' to shape, for example:
 *        0.87
 *   - 'manual-number' to annotations in 'data-annotations':
 *        { name: "K01223", …, manual-number: 0.87 }
 * This data can be removed using resetMap()
 */
function highlightContinuous(
    annotation_to_number,
    colors = ['yellow', 'red']
) {
    resetMap()

    const m_annotations = Object.keys(annotation_to_number)

    function manualShape(shape) {
        let annotations = $(shape).data('annotations')
        let manualNumber

        // for each strain, see if it covers anything
        annotations.forEach(function (annotation, index) {
            if (m_annotations.includes(annotation['name'])) {
                manualNumber = annotation_to_number[annotation['name']]
                annotations[index]['manual-number'] = manualNumber
            }
        })

        if (typeof manualNumber === 'undefined') {
            return  // do nothing
        }

        // write info back to shape
        $(shape).data('manual-number', manualNumber)
        $(shape).data('annotations', annotations)

        // color shape
        shape.firstElementChild.setAttribute('fill', chroma.mix(colors[0], colors[1], manualNumber))
    }

    $(".shape").each(function (index) {
        manualShape(this)
    })
}

/**
 * Returns the annotations that are covered by the shape
 *
 * @param  {Array}  strain_annos Array of annotations, e.g. [ "C00033", "C00031", … ]
 * @param  {Object} shape_annos Array of shape-annotation-objects [ { name="K03103" }, … ]
 * @return {Array}  Array of annotations that are covered by the shape
 */
function getCoveredAnnotations(strain_annos, shape_annos) {
    return shape_annos.filter(item => strain_annos.includes(item['name']))
}

/**
 * Save a map as png, opens save-as dialog
 *
 * @param  {string} element_id ID of an SVG
 */
function saveDivAsPng(element_id) {
    function saveUriAs(uri, filename) {
        var link = document.createElement('a')
        if (typeof link.download === 'string') {
            link.href = uri
            link.download = filename
            //Firefox requires the link to be in the body
            document.body.appendChild(link)
            //simulate click
            link.click()
            //remove the link when done
            document.body.removeChild(link)
        } else {
            window.open(uri)
        }
    }

    html2canvas(document.querySelector("#" + element_id)).then(function (canvas) {
        saveUriAs(canvas.toDataURL(), 'pathway.png')
    })
}

