"use strict"

/**
 * Remove metadata tags from shapes
 *
 * From each shape, remove:
 *   - data-organisms
 *   - data-manual-number
 *   - from each annotation in data-annotations:
 *      - 'organisms'
 *      - 'manual-number
 */
function resetMap() {
    $(".shape").each(function () {
        // make fill transparent
        this.firstElementChild.setAttribute('fill', 'transparent')
        // empty organisms from shape
        $(this).removeData('organisms')
        $(this).removeData('manual-number')
        // empty organisms from annotations
        let annotations = $(this).data('annotations')
        annotations.forEach(function (annotation, index) {
            delete annotations[index]['organisms']
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
 * Colorize shapes by how many organisms have their annotations
 *
 * @param  {Array}  colors Two colors: The first for shapes that are covered by one annotation,
 *   the second for shapes that are covered by all annotations
 * @param  {Object} organisms A dictionary { organism => [ annotation ]}
 *   Example: { Organism1: [ "R09127", "R01788", … ], Organism2: [ … ], … }
 *
 * Adds...
 *   - 'data-organisms' to shape, for example:
 *        { covering: [ "Organism1", … ], not-covering: [] }
 *   - 'organisms' to annotations in 'data-annotations':
 *        { name: "K01223", …, organisms: [ "Organism1", … ] }
 * This data can be removed using resetMap()
 */
function highlightOrganisms(
    organisms,
    colors = ['yellow', 'red']
) {
    resetMap()

    const organism_names = Object.keys(organisms)
    const color_array = chroma.scale(colors).mode('lch').colors(organism_names.length)

    function gradientShape(shape) {
        const annotations = $(shape).data('annotations')
        let covering_organisms = new Set()
        let not_covering_organisms = new Set()
        annotations.forEach(function (annotation, index) {
            annotations[index]['organisms'] = new Set()
        })

        // for each organism, see if it covers anything
        $.each(organisms, function (s_name, s_annotations) {
            let covering = false
            annotations.forEach(function (annotation, index) {
                if (s_annotations.includes(annotation['name'])) {
                    annotations[index]['organisms'].add(s_name)
                    covering_organisms.add(s_name)
                    covering = true
                }
            })
            if (!covering) {
                not_covering_organisms.add(s_name)
            }

        })

        // write info back to shape
        $(shape).data('organisms', {"covering": covering_organisms, "not-covering": not_covering_organisms})
        $(shape).data('annotations', annotations)

        // color shape
        const n_covered = covering_organisms.size
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

        // for each organism, see if it covers anything
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
 * @param  {Array}  organism_annos Array of annotations, e.g. [ "C00033", "C00031", … ]
 * @param  {Object} shape_annos Array of shape-annotation-objects [ { name="K03103" }, … ]
 * @return {Array}  Array of annotations that are covered by the shape
 */
function getCoveredAnnotations(organism_annos, shape_annos) {
    return shape_annos.filter(item => organism_annos.includes(item['name']))
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

