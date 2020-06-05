"use strict";

/**
 * Create context menu with custom contents.
 * Can be used like this:

 let cm = new ClickMenu(event, 'my-context-menu');
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
class ClickMenu {
    constructor(event, menu_id) {
        console.log('run', event, 'ev')
        if (Array.isArray(event)) {
            console.log('create context ref element', event)
            createRefElement(event[0], event[1])
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
            class: 'ogb-click-menu',
            'aria-labelledby': 'dropdownMenuButton',
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

let autoDiscoverSelf = function (event, self_string) {
    if (self_string === 'auto') {
        self_string = $(event.target).text()
    } else {
        assert(typeof self_string === 'string' || self_string instanceof String, 'Error: Could not discover own name.')
    }
    return self_string
}

let autoDiscoverSiblings = function (event, self_string, siblings, type) {
    if (siblings === 'auto') {
        siblings = [self_string]
        $(event.target).siblings().each(function () {
            if ($(this).hasClass(type)) {
                siblings.push($(this).text())
            }
        });
    } else if (typeof (siblings) === 'string') {
        let target = siblings
        siblings = []
        $(target).children().each(function () {
            if ($(this).hasClass(type)) {
                siblings.push($(this).text())
            }
        });
    } else {
        assert(Array.isArray(siblings), 'This function expects an array, a JQuery selector or nothing!!')
    }
    return siblings
}

let autoDiscoverSpecies = function (event, species) {
    if (species === 'auto') {
        species = $(event.target).data('species')
    } else {
        assert(typeof species === 'string' || species instanceof String, 'Error: Could not discover species.')
    }
    return species
}


let showMemberClickMenu = function (event, member = 'auto', species = 'auto', siblings = 'auto') {
    console.log('showMemberClickMenu', 'event:', event, 'member:', member, 'siblings:', siblings)
    // auto-discover species
    species = autoDiscoverSpecies(event, species)

    // auto-discover member
    member = autoDiscoverSelf(event, member)

    // auto-discover siblings
    siblings = autoDiscoverSiblings(event, member, siblings, 'member')

    let cm = new ClickMenu(event, 'member-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header">
${member}</h6>
<a data-species="${species}" href="/taxname/${species}" class="dropdown-item context-menu-icon context-menu-icon-taxid">
${species}</a>
<a href="/member/${member}" class="dropdown-item context-menu-icon context-menu-icon-strain">
Open member info</a>
<a onclick="CopyToClipboard('${member}')" class="dropdown-item context-menu-icon context-menu-icon-copy">
Copy identifier</a>
<a href="/kegg/?members=${member}" class="dropdown-item context-menu-icon context-menu-icon-pathway">
Open member on KEGG map</a>
<a href="/annotation-search/?members=${member}" class="dropdown-item context-menu-icon context-menu-icon-annotation">
Search for annotations in member</a>
<a href="/blast/?members=${member}" class="dropdown-item context-menu-icon context-menu-icon-blast">
Blast member</a>
`)


    if (siblings.length > 1) {
        siblings = siblings.join('+')
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header">
${siblings.length} selected members</h6>
<a href="/trees/?members=${siblings}" class="dropdown-item context-menu-icon context-menu-icon-tree">
Show phylogenetic trees</a>
<a onclick="CopyToClipboard('FAM21277-i1-1.1, FAM19036-p1-1.1, FAM19471-i1-1.1, FAM1079-i1-1.1, FAM22472-i1-1.1')" class="dropdown-item context-menu-icon context-menu-icon-copy">
Copy selected members</a>
<a href="/kegg/?members=${siblings}" class="dropdown-item context-menu-icon context-menu-icon-pathway">
Open members on KEGG map</a>
<a href="/annotation-search/?members=${siblings}" class="dropdown-item context-menu-icon context-menu-icon-annotations">
Search for annotations in members</a>
<a href="/blast/?members=${siblings}" class="dropdown-item context-menu-icon context-menu-icon-blast">
Blast members</a>
</div>
`)
    }
    cm.show();
};


let showAnnotationClickMenu = function (event, annotation = 'auto', siblings = 'auto', members = 'auto') {
    console.log('showAnnotationClickMenu', 'event:', event, 'annotation:', annotation, 'siblings:', siblings, 'members', members)

    // auto-discover annotation
    annotation = autoDiscoverSelf(event, annotation)

    // auto-discover siblings
    siblings = autoDiscoverSiblings(event, annotation, siblings, 'annotation')

    let cm = new ClickMenu(event, 'annotation-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header">
${annotation}</h6>
<a href="/annotation/${annotation}" class="dropdown-item context-menu-icon context-menu-icon-annotation">
Show details about this annotation</a>
<a onclick="CopyToClipboard('${annotation}')" class="dropdown-item context-menu-icon context-menu-icon-copy">
Copy annotation</a>
`)


    if (siblings.length > 1) {
        let siblings_repl = urlReplBlanks(siblings)
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header">
${siblings.length} selected annotations</h6>
<a href="/annotation-search/?annotations=${siblings_repl}" class="dropdown-item context-menu-icon context-menu-icon-annotations">
Search for annotations in annotations</a>
</div>
`)
    }
    cm.show();
};


let showGeneClickMenu = function (event, gene = 'auto', siblings = 'auto') {
    console.log('showGeneClickMenu gene:', event, gene, siblings);

    // auto-discover annotation
    gene = autoDiscoverSelf(event, gene)

    // auto-discover siblings
    siblings = autoDiscoverSiblings(event, gene, siblings, 'gene')

    // initiate context menu
    let cm = new ContextMenu(event, 'gene-context-menu');

    // list of elements to click on
    cm.appendElement(`
<h6 id='gene-context-menu-species-missing' class="dropdown-header context-menu-header">
${gene}</h6>
<a href="/gene/${gene}" class="dropdown-item context-menu-icon context-menu-icon-gene" target="_blank">
Open gene info</a>
`)

    if (siblings.length > 1) {
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header">
${siblings.length} selected genes</h6>
<a href="/compare-genes/?genes=${siblings}" class="dropdown-item context-menu-icon context-menu-icon-annotations">
Compare genes</a>
</div>
`)
    }


    $.getJSON("/api/get-gene", {'gene_identifier': gene}, function (data) {
        console.log('API GET GENE')
        let member = data['member']
        let taxid = data['taxid']
        let species = data['species']
        let annotype_to_gene = data['annotype_to_gene']

        document.getElementById('gene-context-menu-species-missing').setAttribute('data-species', species);

        let html = `
<h6 class="dropdown-header context-menu-header" onclick="showMemberClickMenu(event)">
${member}</h6>
<a href="/member/${member}" class="dropdown-item context-menu-icon context-menu-icon-strain">
Open member info</a>
<h6 class="dropdown-header context-menu-header">
Annotations</h6>
`
        for (const [anno_type, annotations] of Object.entries(annotype_to_gene)) {
            console.log('xxxxxxxxxxxxxxxxxxxxxxxxxxx', anno_type, annotations);
            html += `
<div style="display: inline-flex;">
    <div class="dropdown-item context-menu-icon context-menu-icon-annotations" data-annotype="${annotations[0]['anno_type']}">
    ${annotations[0]['anno_type_verbose']} (${annotations.length})</div>
    <div class="btn-group dropright">
    <button class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="font-size: 1rem; padding: 0rem 0.8rem;">
    </button>
        <div class="dropdown-menu" style="width: 400px">`

            annotations.forEach(a => {
                console.log('anno', a)
                html += `
            <a class="dropdown-item context-menu-icon context-menu-icon-annotation" style="display: flex; flex-wrap: wrap; white-space: inherit" href="/annotation/${a['name']}">
            ${a['name']} (${a['description']})</a>`
            })

            html += `
        </div>
    </div>
</div>`


        }

        cm.appendElement(html)

        cm.popper.update()

    });

    cm.show('top');


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