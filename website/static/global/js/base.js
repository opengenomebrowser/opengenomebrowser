"use strict";

/**
 * Toggle the taxonomy-stylesheet.
 */
function toggle_colorize_tax() {
    let colorize_tax_checkbox = document.getElementById('colorize-tax-checkbox');
    let taxid_color_stylesheet = document.getElementById('taxid-color-stylesheet');

    taxid_color_stylesheet.disabled = !colorize_tax_checkbox.checked;
}

/**
 * Toggle the sequence-viewer-stylesheet.
 */
function toggle_colorize_sequence() {
    let colorize_sequence_checkbox = document.getElementById('colorize-sequence-checkbox');
    let sequence_stylesheet = document.getElementById('sequence-stylesheet');

    sequence_stylesheet.disabled = !colorize_sequence_checkbox.checked;
}

/*
* Capture mous position all the time. Necessary for popups that emerge from canvas/svg.
*/
let jmouseX, jmouseY;
jQuery(document).ready(function () {
    $(document).mousemove(function (e) {
        jmouseX = e.pageX
        jmouseY = e.pageY
    });
});


function assert(condition, message) {
    if (!condition) {
        message = message || "Assertion failed";
        if (typeof Error !== "undefined") {
            throw new Error(message);
        }
        throw message; // Fallback
    }
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
 * });
 */
let waitForElement = function (selector, callback, timeout = 200) {
    if ($(selector).length) {
        callback();
    } else {
        setTimeout(function () {
            waitForElement(selector, callback);
        }, timeout);
    }
};


/*
* This function creates dummy elements. Necessary for popups that emerge from canvas/svg.
*/
let createRefElement = function (marginLeftRight, marginTopBottom) {
    let ref = $('<div>', {
        id: 'ref_box',
        style: `width: ${marginLeftRight * 2}px; height: ${marginTopBottom * 2}px; position: absolute; z-index: -1; top: ${jmouseY - marginTopBottom}px; left: ${jmouseX - marginLeftRight}px`,
    });

    if (!document.getElementById('ref_box')) {
        // create new menu
        ref.appendTo('body');
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
        $t.remove();
        if (fallback !== undefined && fallback) {
            let fs = 'Please, copy the following text:';
            if (window.prompt(fs, text) !== null) return true;
        }
        return false;
    };
    let $t = $('<textarea />');
    $t.val(text).css({
        width: '100px',
        height: '40px'
    }).appendTo('body');
    $t.select();
    try {
        if (document.execCommand('copy')) {
            $t.remove();
            return true;
        }
        fb();
    } catch (e) {
        fb();
    }
};

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function validate_genomes(genomes) {
    return $.getJSON("/api/validate-genomes", {genomes}, function (data) {
    });
}

function validate_pathwaymap(slug) {
    return $.getJSON("/api/validate-pathwaymap", {slug}, function (data) {
    });
}

function validate_annotations(annotations) {
    return $.getJSON("/api/validate-annotations", {annotations}, function (data) {
    });
}

function create_read_only_genome_div(genome_array, genome_to_species, additional_classes = '') {
    let read_only_genome_div = $('<div>', {
        class: "read-only-div " + additional_classes,
        onclick: `CopyToClipboard('${genome_array.join(', ')}')`
    });

    for (let idx in genome_array) {
        read_only_genome_div.append($('<div>', {
            text: genome_array[idx],
            class: 'genome ogb-tag',
            onclick: `showGenomeClickMenu(event)`,
            'data-species': genome_to_species[genome_array[idx]]['sciname'],
            'title': genome_to_species[genome_array[idx]]['sciname'],
            'data-toggle': 'tooltip'
        }).tooltip());
    }

    return read_only_genome_div
}

function create_read_only_annotations_div(annotations_array, annotation_to_type) {
    let read_only_annotations_div = $('<div>', {
        class: "read-only-div",
        css: {'display': 'flex', 'flex-wrap': 'wrap'},
        onclick: `CopyToClipboard('${annotations_array.join(', ')}')`
    });

    for (let idx in annotations_array) {
        read_only_annotations_div.append($('<div>', {
            // class: "dropdown-clickprotect",
            text: annotations_array[idx],
            class: 'annotation ogb-tag',
            onclick: `showAnnotationClickMenu(event, 'auto', 'auto', $(this).parent().parent().parent().parent() )`,
            'data-annotype': annotation_to_type[annotations_array[idx]]['anno_type'],
            'title': annotation_to_type[annotations_array[idx]]['description'],
            'data-toggle': 'tooltip'
        }).tooltip());
    }

    return read_only_annotations_div
}

function init_autocomplete_annotations(div_name) {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-annotations',
            minLength: 2
        },
        forceLowercase: false,
        onChange: on_annotations_change
    });

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0];

    on_annotations_change(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags);
}

function on_annotations_change(field, editor, tags) {
    console.log('field  :', field);
    console.log('editor :', editor);
    console.log('tags   :', tags);

    $.getJSON('/api/annotation-to-type/', {'annotations[]': tags}, function (data) {
        console.log('annotation-to-type', data);

        let annotation_to_type = data;

        let entries = $('li', editor).slice(1);  // remove first placeholder element

        entries.each(function () {
            let li = $(this);
            let anno = li[0].innerText.substring(3);

            console.log('DATA:', data, 'ANNO', anno);
            console.log('DATA:', data[anno]);

            let child_1 = li.children()[1];
            console.log(child_1);
            child_1.setAttribute('data-annotype', data[anno]['anno_type']);
            child_1.setAttribute('data-toggle', 'tooltip');
            child_1.setAttribute('title', data[anno]['description']);
            $(child_1).tooltip();

            let child_2 = li.children()[2];
            child_2.setAttribute('data-annotype', data[anno]['anno_type']);
        });
    });
}

function init_autocomplete_genomes(div_name) {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-genome-identifier/',
            minLength: 2
        },
        forceLowercase: false,
        onChange: on_genomes_change
    });

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0];

    return on_genomes_change(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags);
}

function on_genomes_change(field, editor, tags) {
    console.log('field  :', field);
    console.log('editor :', editor);
    console.log('tags   :', tags);

    $.getJSON('/api/genome-identifier-to-species/', {'genomes[]': tags}, function (data) {
        delete data.success;

        genome_to_species = data;

        let entries = $('li', editor).slice(1);  // remove first placeholder element

        entries.each(function () {
            let li = $(this);
            let genome = li[0].innerText.substring(3);

            // console.log('DATA:', data, 'GENOME', genome);
            // console.log('DATA:', data[genome]);

            let child_1 = li.children()[1];
            child_1.setAttribute('data-species', data[genome]['sciname']);
            child_1.setAttribute('data-toggle', 'tooltip');
            child_1.setAttribute('title', data[genome]['sciname']);
            $(child_1).tooltip();

            let child_2 = li.children()[2];
            child_2.setAttribute('data-species', data[genome]['sciname']);
        });
        return genome_to_species
    });
}


