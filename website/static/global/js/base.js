"use strict"

/**
 * Toggle the taxonomy-stylesheet.
 */
function toggle_colorize_tax() {
    let colorize_tax_checkbox = document.getElementById('colorize-tax-checkbox')
    let taxid_color_stylesheet = document.getElementById('taxid-color-stylesheet')

    taxid_color_stylesheet.disabled = !colorize_tax_checkbox.checked
}

/**
 * Toggle the sequence-viewer-stylesheet.
 */
function toggle_colorize_sequence() {
    let colorize_sequence_checkbox = document.getElementById('colorize-sequence-checkbox')
    let sequence_stylesheet = document.getElementById('sequence-stylesheet')

    sequence_stylesheet.disabled = !colorize_sequence_checkbox.checked
}

/*
* Capture mous position all the time. Necessary for popups that emerge from canvas/svg.
*/
let jmouseX, jmouseY
jQuery(document).ready(function () {
    $(document).mousemove(function (e) {
        jmouseX = e.pageX
        jmouseY = e.pageY
    })
})


function assert(condition, message) {
    if (!condition) {
        message = message || "Assertion failed"
        if (typeof Error !== "undefined") {
            throw new Error(message)
        }
        throw message // Fallback
    }
}

/*
 * Equivalent of Python's rsplit
 */
String.prototype.rsplit = function (sep, maxsplit) {
    let split = this.split(sep);
    return maxsplit ? [split.slice(0, -maxsplit).join(sep)].concat(split.slice(-maxsplit)) : split;
}

/*
 * Encode blanks as !!!, join array
 * E.g. ['OG0000006', 'OG0000010S24', 'S24 family peptidase']
 * becomes "OG0000006+OG0000010S24+S24!!!family!!!peptidase"
 */
let urlReplBlanks = function (arr) {
    let encode = function (str) {
        return str.replaceAll(' ', '!!!')
    }
    return arr.map(str => encode(str)).join('+')
}

/*
 * Undo urlReplBlanks
 * E.g. ['OG0000010S24', 'S24!!!family!!!peptidase']
 * becomes ['OG0000010S24', 'S24 family peptidase']
 */
let undoReplBlanks = function (arr) {
    return arr.map(str => str.replaceAll('!!!', ' '))
}

/*
 * Waits until an element exists
 *
 * Usage:
 * waitForElement(selector, function() {
 *    // work the magic
 * })
 */
let waitForElement = function (selector, callback, timeout = 200) {
    if ($(selector).length) {
        callback()
    } else {
        setTimeout(function () {
            waitForElement(selector, callback)
        }, timeout)
    }
}


/*
* This function creates dummy elements. Necessary for popups that emerge from canvas/svg.
*/
let createRefElement = function (marginLeftRight, marginTopBottom) {
    let ref = $('<div>', {
        id: 'ref_box',
        style: `width: ${marginLeftRight * 2}px; height: ${marginTopBottom * 2}px; position: absolute; z-index: -1; top: ${jmouseY - marginTopBottom}px; left: ${jmouseX - marginLeftRight}px`,
    })

    if (!document.getElementById('ref_box')) {
        // create new menu
        ref.appendTo('body')
    } else {
        // overwrite menu
        $('#ref_box').replaceWith(ref)
    }
}


/**
 * Copies the current selected text to the SO clipboard
 * This method must be called from an event to work with `execCommand()`
 * @param {String} text Text to copy
 * @param {Boolean} [fallback] Set to true shows a prompt
 * @return Boolean Returns `true` if the text was copied or the user clicked on accept (in prompt), `false` otherwise
 */
let CopyToClipboard = function (text, fallback) {
    let fb = function () {
        $t.remove()
        if (fallback !== undefined && fallback) {
            let fs = 'Please, copy the following text:'
            if (window.prompt(fs, text) !== null) return true
        }
        return false
    }
    let $t = $('<textarea />')
    $t.val(text).css({
        width: '100px',
        height: '40px'
    }).appendTo('body')
    $t.select()
    try {
        if (document.execCommand('copy')) {
            $t.remove()
            return true
        }
        fb()
    } catch (e) {
        fb()
    }
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

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

function validate_genomes(genomes) {
    return $.getJSON("/api/validate-genomes", {genomes}, function (data) {
    })
}

function validate_genes(genes) {
    return $.getJSON("/api/validate-genes", {genes}, function (data) {
    })
}

function validate_pathwaymap(slug) {
    return $.getJSON("/api/validate-pathwaymap", {slug}, function (data) {
    })
}

function validate_annotations(annotations) {
    return $.getJSON("/api/validate-annotations", {annotations}, function (data) {
    })
}

function create_read_only_genome_div(genome_array, genome_to_species, additional_classes = '', click_menu_annotation = 'auto') {
    console.log('click_menu_annotations', click_menu_annotation)
    let read_only_genome_div = $('<div>', {
        class: "read-only-div " + additional_classes,
        onclick: `CopyToClipboard('${genome_array.join(', ')}')`
    })

    for (const genome of genome_array) {
        if (!(genome in genome_to_species)) {
            console.log(genome, 'not in genome_to_species!')
        }
        read_only_genome_div.append($('<div>', {
            text: genome,
            class: 'genome ogb-tag',
            onclick: `showGenomeClickMenu(event, 'auto', 'auto', 'auto', '${click_menu_annotation}')`,
            'data-species': genome_to_species[genome]['sciname'],
            'title': genome_to_species[genome]['sciname']
        }).tooltip())
    }

    return read_only_genome_div
}

function create_read_only_annotations_div(annotations_array, annotation_to_type) {
    let read_only_annotations_div = $('<div>', {
        class: "read-only-div",
        css: {'display': 'flex', 'flex-wrap': 'wrap'},
        onclick: `CopyToClipboard('${annotations_array.join(', ')}')`
    })

    for (let idx in annotations_array) {
        read_only_annotations_div.append($('<div>', {
            // class: "dropdown-clickprotect",
            text: annotations_array[idx],
            class: 'annotation ogb-tag',
            onclick: `showAnnotationClickMenu(event, 'auto', 'auto', $(this).parent().parent().parent().parent() )`,
            'data-annotype': annotation_to_type[annotations_array[idx]]['anno_type'],
            'title': annotation_to_type[annotations_array[idx]]['description']
        }).tooltip())
    }

    return read_only_annotations_div
}

function init_autocomplete_annotations(div_name) {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-annotations',
            minLength: 0
        },
        forceLowercase: false,
        onChange: on_annotations_change
    })

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0]

    on_annotations_change(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)
}

function on_annotations_change(field, editor, tags) {
    console.log('field  :', field)
    console.log('editor :', editor)
    console.log('tags   :', tags)

    $.getJSON('/api/annotation-to-type/', {'annotations[]': tags}, function (data) {
        console.log('annotation-to-type', data)

        let annotation_to_type = data

        let entries = $('li', editor).slice(1)  // remove first placeholder element

        entries.each(function () {
            let li = $(this)
            let anno = li[0].innerText.substring(3)

            let child_1 = li.children()[1]
            child_1.setAttribute('data-annotype', data[anno]['anno_type'])
            child_1.setAttribute('title', data[anno]['description'])
            $(child_1).tooltip()

            let child_2 = li.children()[2]
            child_2.setAttribute('data-annotype', data[anno]['anno_type'])
        })
    })
}

function init_autocomplete_genomes(div_name) {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-genomes/',
            minLength: 0
        },
        forceLowercase: false,
        onChange: on_genomes_change
    })

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0]

    return on_genomes_change(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)
}

function on_genomes_change(field, editor, tags) {
    console.log('field  :', field)
    console.log('editor :', editor)
    console.log('tags   :', tags)

    $.getJSON('/api/genome-identifier-to-species/', {'genomes[]': tags}, function (data) {
        delete data.success

        genome_to_species = data

        let entries = $('li', editor).slice(1)  // remove first placeholder element

        entries.each(function () {
            let li = $(this)
            let genome = li[0].innerText.substring(3)
            let genome_data = data[genome]

            console.log('XXXXXXXXXXXXXXXXXXXXXXXXx', genome, genome_data)

            let child_1 = li.children()[1]
            let child_2 = li.children()[2]

            if (genome_data['type'] === 'taxid' || genome_data['type'] === 'genome') {
                child_1.setAttribute('data-species', genome_data['sciname'])
                child_1.setAttribute('title', genome_data['sciname'])
                child_2.setAttribute('data-species', genome_data['sciname'])
            } else if (genome_data['type'] === 'tag') {
                child_1.setAttribute('data-tag', genome_data['tag'])
                child_1.setAttribute('title', genome_data['description'])
                child_2.setAttribute('data-tag', genome_data['tag'])
            } else {
                console.log('ERROR in on_genomes_change!', genome, genome_data, li)
            }

            $(child_1).tooltip()
        })
        return genome_to_species
    })
}

function init_autocomplete_genes(div_name) {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-genes/',
            minLength: 0
        },
        forceLowercase: false,
        onChange: on_genes_change
    })

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0]

    return on_genes_change(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)
}

function on_genes_change(field, editor, tags) {
    console.log('field  :', field)
    console.log('editor :', editor)
    console.log('tags   :', tags)

    const genomes = Array.from(new Set(tags.map(function (gene) {
        return gene.rsplit('_', 1)[0]
    })))

    $.getJSON('/api/genome-identifier-to-species/', {'genomes[]': genomes}, function (data) {
        delete data.success

        genome_to_species = data

        let entries = $('li', editor).slice(1)  // remove first placeholder element

        entries.each(function () {
            const li = $(this)
            const gene = li[0].innerText.substring(3)
            const genome = gene.rsplit('_', 1)[0]

            let child_1 = li.children()[1]
            child_1.setAttribute('data-species', data[genome]['sciname'])
            child_1.setAttribute('title', data[genome]['sciname'])
            $(child_1).tooltip()

            let child_2 = li.children()[2]
            child_2.setAttribute('data-species', data[genome]['sciname'])
        })

        return genome_to_species
    })
}
