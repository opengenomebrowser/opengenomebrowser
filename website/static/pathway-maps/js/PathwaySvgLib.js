"use strict"

function calcColorArray(nSteps, colors) {
    if (nSteps === 1) {
        return [colors[0], colors[colors.length-1]]
    } else {
        if (colors.length === 4) {
            return [colors[0]].concat(chroma.scale([colors[1], colors[2]]).mode('lch').colors(nSteps - 1)).concat([colors[3]])
        } else {
            return [colors[0]].concat(chroma.scale([colors[1], colors[2]]).mode('lch').colors(nSteps))
        }
    }
}

/**
 * Remove metadata tags from shapes
 *
 * From each shape, remove:
 *   - data-organisms
 *   - data-manual-number
 *   - from each annotation in data-annotations:
 *      - 'organisms'
 *      - 'manual-number
 *
 * Restores fill/stroke to transparent.
 *
 * @param svg {Object} target svg element
 */
function resetMap(svg) {
    $(svg).find('.shape').each(function (i, shape) {
        // make fill/stroke transparent
        colorShape(shape, 'transparent')
        // empty organisms from shape
        $(shape).removeData('organisms')
        $(shape).removeData('manual-number')
        // empty organisms from annotations
        let annotations = $(shape).data('annotations')
        annotations.forEach(function (annotation, index) {
            delete annotations[index]['organisms']
            delete annotations[index]['manual-number']
        })
        $(this).data('annotations', annotations)
    })

    // delete defs element if it exists
    $(svg).find('#shape-color-defs').each(function (i, element) {
        element.remove()
    })
}

/**
 * Colorize shapes by whether they cover certain annotations
 *
 * @param svg {Object} target svg element
 * @param  {string} color The color for covered shapes
 * @param  {Array}  annotations_to_highlight Array of annotations to highlight
 */
function highlightBinary(
    svg,
    color = 'red',
    annotations_to_highlight = []  // e.g. ['K00001']
) {
    resetMap(svg)

    $('.shape').each(function () {
        let annotations = $(this).data('annotations')
        if (getCoveredAnnotations(annotations_to_highlight, annotations).length) {
            colorShape(this, color)
        } else {
            colorShape(this, 'transparent')
        }
    })
}

/**
 * Colorize shapes by how many organisms have their annotations
 *
 * @param svg {Object} target svg element
 * @param  {Array}  colors Two colors: The first for shapes that are covered by one annotation,
 *   the second for shapes that are covered by all annotations
 * @param  {Object} organisms A dictionary { organism => [ annotation ]}
 *   Example: { Organism1: [ "R09127", "R01788", … ], Organism2: [ … ], … }
 *
 * Adds...
 *   - 'data-organisms' to shape, for example:
 *        { covering: [ "Organism1", … ], not-covering: [] }
 *   - 'organisms' to annotations in 'data-annotations':
 *        { name: "K01223", …, organisms: { covering: [ "Organism1", … ], not-covering: [] } }
 *
 * Changes fill/stroke to a color.
 *
 * This data can be removed using resetMap()
 */
function highlightOrganisms(
    svg,
    organisms,
    colors = ['transparent', 'yellow', 'red', 'green']
) {
    resetMap(svg)

    let organismNames = Object.keys(organisms)
    let colorArray = calcColorArray(organismNames.length, colors)

    function singleColorShape(shape) {
        let annotations = $(shape).data('annotations')
        let coveringOrganisms = new Set()
        let notCoveringOrganisms = new Set()
        annotations.forEach(function (annotation, index) {
            annotations[index]['organisms'] = {'covering': new Set(), 'not-covering': new Set()}
        })
        let dataOrganisms = {'covering': new Set(), 'not-covering': new Set()}

        // for each organism, see if it covers anything
        $.each(organisms, function (o_name, o_annotations) {
            let covering = false
            annotations.forEach(function (annotation, index) {
                if (o_annotations.includes(annotation['name'])) {
                    annotations[index]['organisms']['covering'].add(o_name)
                    covering = true
                } else {
                    annotations[index]['organisms']['not-covering'].add(o_name)
                }
            })
            if (covering) {
                dataOrganisms['covering'].add(o_name)
            } else {
                dataOrganisms['not-covering'].add(o_name)
            }

        })

        // write info back to shape
        $(shape).data('organisms', dataOrganisms)
        $(shape).data('annotations', annotations)

        // color shape
        colorShape(shape, colorArray[dataOrganisms['covering'].size])
    }

    $('.shape').each(function (index) {
        singleColorShape(this)
    })
}

/**
 * Colorize shapes by how many organisms have their annotations
 *
 * @param svg {Object} target svg element
 * @param  {Array}  colors Two colors: The first for shapes that are covered by one annotation,
 *   the second for shapes that are covered by all annotations
 * @param  {Object} groupsOfOrganisms A dictionary of organism dictionaries {group => { organism => [ annotation ]} }
 *   Example: { Group1: { Organism1: [ "R09127", "R01788", … ], Organism2: [ … ], … }, Group2: {…} }
 *
 * Adds...
 *   - 'data-organisms' to shape, for example:
 *        { covering: { Group1: [ "Organism1", … ], Group2: []}}, not-covering: { Group1: [], Group2: ["OrganismA"] }
 *   - 'organisms' to annotations in 'data-annotations':
 *        { name: "K01223", …, organisms: [ "Organism1", … ] }
 *   - LinearGradient defs to SVG
 *
 * Changes fill/stroke to a LinearGradient.
 *
 * This data can be removed using resetMap()
 */
function highlightGroupsOfOrganisms(
    svg,
    groupsOfOrganisms,
    colors = ['transparent', 'yellow', 'red', 'green']
) {
    resetMap(svg)

    const nGroups = Object.keys(groupsOfOrganisms).length

    // calculate color gradient for all groups of organisms
    let groupColorArrays = {}
    for (const [groupName, organisms] of Object.entries(groupsOfOrganisms)) {
        groupColorArrays[groupName] = calcColorArray(Object.keys(organisms).length, colors)
    }

    // create svg defs element to store gradients
    let defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs')
    defs.id = 'shape-color-defs'

    function multicolorShape(shape, shapeIndex) {
        let groupColors = {}
        let annotations = $(shape).data('annotations')
        let coveringOrganismGroups = {}
        let notCoveringOrganismGroups = {}

        annotations.forEach(function (annotation, index) {
            annotations[index]['organisms'] = Object.keys(groupsOfOrganisms).reduce(function (obj, groupName) {
                obj[groupName] = {'covering': new Set(), 'not-covering': new Set()}
                return obj
            }, {})
        })
        let dataOrganisms = {}

        for (const [groupName, organisms] of Object.entries(groupsOfOrganisms)) {
            dataOrganisms[groupName] = {'covering': new Set(), 'not-covering': new Set()}

            // for each organism, see if it covers anything
            $.each(organisms, function (o_name, o_annotations) {
                let covering = false
                annotations.forEach(function (annotation, index) {
                    if (o_annotations.includes(annotation['name'])) {
                        annotations[index]['organisms'][groupName]['covering'].add(o_name)
                        covering = true
                    } else {
                        annotations[index]['organisms'][groupName]['not-covering'].add(o_name)
                    }
                })
                if (covering) {
                    dataOrganisms[groupName]['covering'].add(o_name)
                } else {
                    dataOrganisms[groupName]['not-covering'].add(o_name)
                }
            })

            // write info back to shape
            groupColors[groupName] = groupColorArrays[groupName][dataOrganisms[groupName]['covering'].size]
        }

        // write info back to shape
        $(shape).data('organisms', dataOrganisms)
        $(shape).data('annotations', annotations)

        // color shape
        if (nGroups === 1) {
            colorShape(shape, Object.values(groupColors)[0])
        } else {
            let gradient = createGradient(groupColors, nGroups, shape)
            gradient.id = 'gradient-shape-' + shapeIndex
            defs.appendChild(gradient)
            colorShape(shape, `url(#gradient-shape-${shapeIndex})`)
        }
    }

    $(svg).find('.shape').each(function (index) {
        multicolorShape(this, index)
    })

    svg.appendChild(defs)
}

/**
 * Create a SVG linear gradient
 *
 * @param  {Array}  groupColors A list of colors, one per group
 * @param  {number} nGroups The number of groups
 * @param  {Object} targetElement The element the gradient will be applied to
 * @return {Object} gradient An SVG gradient element
 */
function createGradient(groupColors, nGroups, targetElement) {
    let gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient')
    const protoStops = Array(nGroups + 1).fill().map((_, index) => index / nGroups * 100 + '%')
    let stops = []
    Object.values(groupColors).forEach(function (color, i) {
        stops.push({'color': color, 'offset': protoStops[i]}, {'color': color, 'offset': protoStops[i + 1]})
    })
    stops.shift()  // remove first element (not important)
    stops.pop()    // remove last element (not important)

    // Create stop elements
    for (var i = 0, length = stops.length; i < length; i++) {
        let stop = document.createElementNS('http://www.w3.org/2000/svg', 'stop')
        stop.setAttribute('offset', stops[i].offset)
        stop.setAttribute('stop-color', stops[i].color)
        gradient.appendChild(stop)
    }

    // set gradient direction
    // gradient.setAttribute('x2', '1') // ->  does not work for elements with width or height = 0, wtf?!
    const bbox = targetElement.getBBox()
    gradient.setAttribute('gradientUnits', 'userSpaceOnUse')
    gradient.setAttribute('x1', bbox['x'])
    gradient.setAttribute('x2', bbox['x'] + bbox['width'])

    return gradient
}


/**
 * Colorize shapes by continuous numbers between 0 and 1
 *
 * @param svg {Object} target svg element
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
 *
 * Changes fill to a color.
 *
 * This data can be removed using resetMap()
 */
function highlightContinuous(
    svg,
    annotation_to_number,
    colors = ['yellow', 'red']
) {
    resetMap(svg)

    const myAnnotations = Object.keys(annotation_to_number)

    function manualShape(shape) {
        let annotations = $(shape).data('annotations')
        let manualNumber

        // for each organism, see if it covers anything
        annotations.forEach(function (annotation, index) {
            if (myAnnotations.includes(annotation['name'])) {
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
        colorShape(shape, chroma.mix(colors[0], colors[1], manualNumber))
    }

    $('.shape').each(function (index) {
        manualShape(this)
    })
}

/**
 * Changes the fill or stroke attribute of a shape.
 *
 * The value is set to the attribute specified by 'data-apply-color-to'.
 * If 'data-apply-color-to' is not set, the 'fill' attribute will be changed.
 *
 * @param  {Object} shape Shape svg element
 * @param  {string} attributeValue color or url to definition, e.g. 'red' or 'url(#gradient-shape-0)'
 */
function colorShape(shape, attributeValue) {
    let targetAttribute = $(shape).data('apply-color-to')
    targetAttribute = targetAttribute === undefined ? 'fill' : targetAttribute
    shape.setAttribute(targetAttribute, attributeValue)
}

/**
 * Returns the annotations that are covered by the shape
 *
 * @param  {Array}  OrganismAnnotations Array of annotations, e.g. [ "C00033", "C00031", … ]
 * @param  {Object} ShapeAnnotations Array of shape-annotation-objects [ { name="K03103" }, … ]
 * @return {Array}  Array of annotations that are covered by the shape
 */
function getCoveredAnnotations(OrganismAnnotations, ShapeAnnotations) {
    return ShapeAnnotations.filter(item => OrganismAnnotations.includes(item['name']))
}

/**
 * Opens save-as dialog
 *
 * @param  {string} uri Content to download
 * @param  {string} filename Desired filename
 */
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

/**
 * Save a map as png, opens save-as dialog
 *
 * @param  {Object} element Div to save as png
 * @param filename default: download.png
 */
function savePng(element, filename='download.png') {
    $(window).scrollTop(0)  // otherwise, png will be cropped.
    html2canvas(element).then(function (canvas) {
        saveUriAs(canvas.toDataURL(), filename)
    })
}

/**
 * Save a map as svg, opens save-as dialog
 *
 * @param svg {Object} target svg element
 * @param filename default: download.svg
 */
function saveSvg(svg, filename='download.svg') {
    //serialize svg.
    let serializer = new XMLSerializer()
    console.log('svg', svg)
    let data = serializer.serializeToString(svg)
    data = encodeURIComponent(data)

    // add file type declaration
    data = 'data:image/svg+xml;charset=utf-8,' + data

    saveUriAs(data, filename)
}