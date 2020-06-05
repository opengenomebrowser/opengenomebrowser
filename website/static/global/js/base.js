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
* This function creates dummy elements. Necessary for popups that emerge from canvas/svg.
*/
let createContextRefElement = function (marginLeftRight, marginTopBottom) {
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

/**
 * Create context menu with custom contents.
 * Can be used like this:

 let cm = new ContextMenu(event, temp0);
 let some_element = $('<a>', {
    class: "dropdown-item",  // important: prevents collapse on click
    href: "https://www.example.com",
    target: "_blank",
    text: "Example Dot Com",
 });
 cm.appendElement(some_element);
 cm.appendSeparator();
 // event.stopPropagation();
 cm.show();

 */
class ContextMenu {
    constructor(event, menu_id) {
        console.log('run', event, 'ev')
        if (Array.isArray(event)) {
            console.log('create context ref element', event)
            createContextRefElement(event[0], event[1])
            this.target = $('#ref_box')
        } else {
            console.log('stop event', event)
            event.preventDefault();
            event.stopPropagation()
            this.target = event.target
        }
        this.menu_id = menu_id;
        this.createMenu(this.menu_id);
        this.dropdown = $('#' + this.menu_id);
        this.popper = null;

        this.dropdown_separator_div = $('<div>', {
            class: 'dropdown-divider'
        });
    }

    createMenu = function (id) {
        let new_menu = $('<div>', {
            id: id,
            display: 'flex',
            class: 'dropdown',
            'aria-labelledby': 'dropdownMenuButton',
            css: {
                'background-color': 'white',
                padding: '.5rem 0',
                border: '1px solid rgba(0,0,0,.15)',
                display: 'flex',
                'flex-direction': 'column',
                'max-width': '400px',
                'min-width': '250px'
            },
        });
        if (!document.getElementById(id)) {
            // create new menu
            new_menu.appendTo('body');
        } else {
            // overwrite menu
            $('#' + id).replaceWith(new_menu)
        }
    };

    appendElement = function (element) {
        this.dropdown.append(element);
    };

    appendSeparator = function () {
        this.dropdown.append(this.dropdown_separator_div)
    };

    appendHeader = function (text) {
        this.dropdown.append($('<h6>', {
                text: text, class: 'dropdown-header context-menu-header'
            })
        )
    };

    // add listener (to close the menu), place and show it.
    show = function (placement = 'bottom') {
        let mydropdown = this.dropdown;
        let menu_id = this.menu_id;

        // add the kegg-menu to the page, place it below relative_element
        this.popper = new Popper(this.target, this.dropdown,
            {
                placement: placement,
                modifiers: {
                    eventsEnabled: {enabled: true},
                },
            });

        console.log('show', this.dropdown)

        this.dropdown.show();

        // add listener to close the menu
        $(document).on('click.context-menu-event', function (e) {
            // console.log('context-menu listener speaking. target:', e.target);

            if (e.altKey || e.metaKey || $('#' + menu_id).has(e.target).length == 1 || $('#' + menu_id).is(e.target)) {
                // ignore clicks with alt or meta keys
                // ignore clicks on dropdown
            } else {
                // hide div
                console.log('hide context menu')
                mydropdown.hide();
            }
        });
    };
}

/**
 * Create context menu for a Member.
 * Can be used like this:

 ShowMemberContextMenu(event, member_identifier)
 or:
 ShowMemberContextMenu(event, member_identifier, [sibling-id-1, sibling-id-2, ...])

 */
let ShowMemberContextMenu = function (event, member, siblings = 'auto') {
    console.log('ShowMemberContextMenu', 'event:', event, 'member:', member, 'siblings:', siblings);

    // auto-discover siblings
    if (siblings === 'auto') {
        console.log('autodiscover')

        siblings = [member]
        $(event.target).siblings().each(function () {
            if ($(this).hasClass('member')) {
                siblings.push($(this).text())
            }
        });
    } else if (typeof (siblings) === 'string') {
        console.log('autodiscover')
        let target = siblings
        siblings = []
        $(target).children().each(function () {
            if ($(this).hasClass('member')) {
                siblings.push($(this).text())
            }
        });

    } else {
        assert(Array.isArray(siblings), 'This function expects an array, a JQuery selector or nothing!!')
    }

    let cm = new ContextMenu(event, 'member-context-menu');

    // list of elements to click on
    cm.appendHeader(member);

    cm.appendElement($('<a>', {
        text: 'Open member info',
        href: `/member/${member}`,
        class: "dropdown-item context-menu-icon context-menu-icon-strain", target: "_blank"
    }));

    cm.appendElement($('<a>', {
        text: 'Copy identifier',
        onclick: `CopyToClipboard('${member}')`,
        class: "dropdown-item context-menu-icon context-menu-icon-copy", target: "_blank"
    }));

    cm.appendElement($('<a>', {
        text: 'Open member on KEGG map',
        href: `/kegg/?members=${member}`,
        class: "dropdown-item context-menu-icon context-menu-icon-pathway", target: "_blank"
    }));

    cm.appendElement($('<a>', {
        text: 'Search for annotations in member',
        href: `/annotation-search/?members=${member}`,
        class: "dropdown-item context-menu-icon context-menu-icon-annotation", target: "_blank"
    }));

    cm.appendElement($('<a>', {
        text: 'Blast member',
        href: `/blast/?members=${member}`,
        class: "dropdown-item context-menu-icon context-menu-icon-blast", target: "_blank"
    }));


    if (siblings.length > 1) {
        cm.appendHeader(`${siblings.length} selected members`);

        cm.appendElement($('<a>', {
            text: 'Show phylogenetic trees',
            href: `/trees/?members=${siblings.join('+')}`,
            class: "dropdown-item context-menu-icon context-menu-icon-tree", target: "_blank"
        }));

        cm.appendElement($('<a>', {
            text: 'Copy selected members',
            onclick: `CopyToClipboard('${siblings.join(', ')}')`,
            class: "dropdown-item context-menu-icon context-menu-icon-copy", target: "_blank"
        }));

        cm.appendElement($('<a>', {
            text: 'Open members on KEGG map',
            href: `/kegg/?members=${siblings.join('+')}`,
            class: "dropdown-item context-menu-icon context-menu-icon-pathway", target: "_blank"
        }));

        cm.appendElement($('<a>', {
            text: 'Search for annotations in members',
            href: `/annotation-search/?members=${siblings.join('+')}`,
            class: "dropdown-item context-menu-icon context-menu-icon-annotations", target: "_blank"
        }));

        cm.appendElement($('<a>', {
            text: 'Blast members',
            href: `/blast/?members=${siblings.join('+')}`,
            class: "dropdown-item context-menu-icon context-menu-icon-blast", target: "_blank"
        }));
    }

    cm.show();
};

/**
 * Create context menu for an Annotation.
 * Can be used like this:

 ShowAnnotationContextMenu(event, annotation)
 or:
 ShowAnnotationContextMenu(event, annotation, [sibling-id-1, sibling-id-2, ...])
 */
let ShowAnnotationContextMenu = function (event, annotation, siblings = 'auto') {
    console.log('ShowAnnotationContextMenu', 'event:', event, 'annotation:', annotation, 'siblings:', siblings);

    // auto-discover siblings
    if (siblings === 'auto') {
        console.log('autodiscover')

        siblings = [annotation]
        $(event.target).siblings().each(function () {
            if ($(this).hasClass('annotation')) {
                siblings.push($(this).text())
            }
        });
    } else if (typeof (siblings) === 'string') {
        console.log('autodiscover')
        let target = siblings
        siblings = []
        $(target).children().each(function () {
            if ($(this).hasClass('member')) {
                siblings.push($(this).text())
            }
        });

    } else {
        assert(Array.isArray(siblings), 'This function expects an array, a JQuery selector or nothing!!')
    }

    let cm = new ContextMenu(event, 'annotation-context-menu');

    // list of elements to click on
    cm.appendHeader(annotation);

    let annolink = urlReplBlanks([annotation])

    cm.appendElement($('<a>', {
        text: 'Search genes',
        href: `/annotation-search/?annotations=${annolink}`,
        class: "dropdown-item context-menu-icon context-menu-icon-annotation", target: "_blank"
    }));

    cm.appendElement($('<a>', {
        text: 'Copy name',
        onclick: `CopyToClipboard('${annotation}')`,
        class: "dropdown-item context-menu-icon context-menu-icon-copy", target: "_blank"
    }));

    if (siblings.length > 1) {
        cm.appendHeader(`${siblings.length} selected annotations`);

        let siblingslink = urlReplBlanks(siblings)

        cm.appendElement($('<a>', {
            text: 'Search genes',
            href: `/annotation-search/?annotations=${siblingslink}`,
            class: "dropdown-item context-menu-icon context-menu-icon-tree", target: "_blank"
        }));


        cm.appendElement($('<a>', {
            text: 'Copy selected annotations',
            onclick: `CopyToClipboard('${siblings.join(', ')}')`,
            class: "dropdown-item context-menu-icon context-menu-icon-copy", target: "_blank"
        }));
    }

    cm.show();
};


/**
 * Create context menu for a Gene.
 * Can be used like this:

 ShowGeneContextMenu(event, gene_identifier)

 */
let ShowGeneContextMenu = function (event, gene_identifier) {
    console.log('ShowGeneContextMenu gene:', event, gene_identifier);

    // initiate context menu
    let cm = new ContextMenu(event, 'gene-context-menu');

    // list of elements to click on
    cm.appendHeader(gene_identifier);

    cm.appendElement($('<a>', {
        text: 'Open gene info',
        href: `/gene/${gene_identifier}`,
        class: "dropdown-item context-menu-icon context-menu-icon-world", target: "_blank"
    }));

    $.getJSON("/api/get-gene", {gene_identifier}, function (data) {
        cm.appendHeader('Member');
        cm.appendElement($('<p>', {
            class: "dropdown-item context-menu-icon context-menu-icon-strain", target: "_blank"
        }).append(data['member_html']));

        cm.appendHeader('Annotations');

        for (let idx in data['annotations']) {
            cm.appendElement($('<p>', {
                class: "dropdown-item context-menu-icon context-menu-icon-annotation", target: "_blank"
            }).append(data['annotations'][idx]['html']));
        }

        cm.popper.update()

        $('#context-menu [data-toggle="tooltip"]').tooltip({
            title: function () {
                return $(this).attr('data-species');
            }
        })

    });

    cm.show('top');


};


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function validate_members(members) {
    return $.getJSON("/api/validate-members", {members}, function (data) {
    });
}

function validate_keggmap(map_id) {
    return $.getJSON("/api/validate-keggmap", {map_id}, function (data) {
    });
}

function validate_annotations(annotations) {
    return $.getJSON("/api/validate-annotations", {annotations}, function (data) {
    });
}

function create_read_only_strain_div(strain_array, member_to_species) {
    let read_only_strain_div = $('<div>', {
        class: "read-only-div",
        css: {'display': 'flex', 'flex-wrap': 'wrap'},
        onclick: `CopyToClipboard('${strain_array.join(', ')}')`
    });

    for (let idx in strain_array) {
        read_only_strain_div.append($('<div>', {
            // class: "dropdown-clickprotect",
            text: strain_array[idx],
            class: 'member ogb-tag',
            onclick: `ShowMemberContextMenu(event, '${strain_array[idx]}')`,
            'data-species': member_to_species[strain_array[idx]]['sciname'],
            'title': member_to_species[strain_array[idx]]['sciname'],
            'data-toggle': 'tooltip'
        }).tooltip());
    }

    return read_only_strain_div
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
            onclick: `ShowAnnotationContextMenu(event, '${annotations_array[idx]}')`,
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

function init_autocomplete_members(div_name) {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-genome-identifier/',
            minLength: 2
        },
        forceLowercase: false,
        onChange: on_members_change
    });

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0];

    return on_members_change(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags);
}

function on_members_change(field, editor, tags) {
    console.log('field  :', field);
    console.log('editor :', editor);
    console.log('tags   :', tags);

    $.getJSON('/api/member-identifier-to-species/', {'members[]': tags}, function (data) {
        delete data.success;

        member_to_species = data;

        let entries = $('li', editor).slice(1);  // remove first placeholder element

        entries.each(function () {
            let li = $(this);
            let member = li[0].innerText.substring(3);

            // console.log('DATA:', data, 'MEMBER', member);
            // console.log('DATA:', data[member]);

            let child_1 = li.children()[1];
            child_1.setAttribute('data-species', data[member]['sciname']);
            child_1.setAttribute('data-toggle', 'tooltip');
            child_1.setAttribute('title', data[member]['sciname']);
            $(child_1).tooltip();

            let child_2 = li.children()[2];
            child_2.setAttribute('data-species', data[member]['sciname']);
        });
        return member_to_species
    });
}
