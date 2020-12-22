"use strict"

/*
 * Contains id's of context-menus.
 * The most recently clicked is at the end of the queue.
 * See ClickMenu.reorder()
 */
let contextMenuQueue = []

/**
 * Create context menu with custom contents.
 * Can be used like this:

 let cm = new ClickMenu(event, 'my-context-menu')
 let some_element = $('<a>', {
    class: "dropdown-item",  // important: prevents collapse on click
    href: "https://www.example.com",
    target: "_blank",
    text: "Example Dot Com",
 })
 cm.appendElement(some_element)
 cm.appendSeparator()
 // event.stopPropagation()
 cm.show()
 */
class ClickMenu {
    constructor(event, menu_id) {
        if (Array.isArray(event)) {
            createRefElement(event[0], event[1])
            this.target = $('#ref_box')
        } else {
            event.preventDefault()
            event.stopPropagation()
            this.target = event.target
        }
        this.menu_id = menu_id
        this.createMenu(this.menu_id)
        this.dropdown = $('#' + this.menu_id)
        this.popper = null

        this.dropdown_separator_div = $('<div>', {
            class: 'dropdown-divider'
        })
    }

    createMenu = function (id) {
        let new_menu = $('<div>', {
            id: id,
            display: 'flex',
            class: 'ogb-click-menu',
            'aria-labelledby': 'dropdownMenuButton',
        })
        if (!document.getElementById(id)) {
            // create new menu
            new_menu.appendTo('body')
        } else {
            // overwrite menu
            $('#' + id).replaceWith(new_menu)
        }
    }

    reorder = function () {
        // ensure the most recently clicked menu is on top
        // remove this.menu from the list and add it to the end of the queue
        const index = contextMenuQueue.indexOf(this.menu_id);
        if (index > -1) {
            contextMenuQueue.splice(index, 1);
        }
        contextMenuQueue.push(this.menu_id)

        // set z-index accordingly, starting at z-index 10
        for (const [idx, menu_id] of Object.entries(contextMenuQueue)) {
            document.getElementById(menu_id).style.zIndex = 10 + idx
        }

    }

    appendElement = function (element) {
        this.dropdown.append(element)
    }

    appendSeparator = function () {
        this.dropdown.append(this.dropdown_separator_div)
    }

    appendHeader = function (text) {
        this.dropdown.append($('<h6>', {
                text: text, class: 'dropdown-header context-menu-header'
            })
        )
    }

    // add listener (to close the menu), place and show it.
    show = function (placement = 'bottom') {
        let mydropdown = this.dropdown
        let menu_id = this.menu_id

        // add the click-menu to the page, place it below relative_element
        this.popper = new Popper(this.target, this.dropdown,
            {
                placement: placement,
                modifiers: {
                    eventsEnabled: {enabled: true},
                },
            })

        if (!contextMenuQueue.includes(menu_id)) {
            // add listener to close the menu (only one listener for every menu_id)
            $(document).on('click.context-menu-event', function (e) {

                if (e.altKey || e.metaKey || e.which === 3 || $('#' + menu_id).has(e.target).length == 1 || $('#' + menu_id).is(e.target)) {
                    // ignore clicks with alt or meta keys
                    // ignore clicks on dropdown
                } else {
                    // hide div
                    $('#' + menu_id).hide()
                }
            })

            contextMenuQueue.push(menu_id)

        }

        this.reorder()

        this.dropdown.show()
    }
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
    if (siblings instanceof jQuery) {
        return siblings.find('.' + type).map(function () {
            return $(this).text()
        }).get()
    } else if (siblings === 'auto') {
        if (self_string === undefined) {
            siblings = []
        } else {
            siblings = [self_string]
        }

        $(event.target).siblings().each(function () {
            if ($(this).hasClass(type)) {
                siblings.push($(this).text())
            }
        })
    } else if (typeof (siblings) === 'string') {
        let target = siblings
        siblings = []
        $(target).find('.' + type).each(function () {
            siblings.push($(this).text())
        })
    } else {
        assert(Array.isArray(siblings), 'This function expects an array, a JQuery selector or nothing!!')
    }
    return siblings
}

let autoDiscoverSpecies = function (event, species) {
    if (species === 'auto') {
        species = $(event.target).data('species')
    } else if (species === 'none') {
        species = false
    } else {
        assert(typeof species === 'string' || species instanceof String, 'Error: Could not discover species.')
    }
    return species
}

let autoDiscoverGenomes = function (genomes) {
    if (genomes === 'none') {
        return []
    } else if (Array.isArray(genomes)) {
        return genomes
    } else if (genomes instanceof jQuery) {
        return genomes.find('.genome').map(function () {
            return $(this).text()
        }).get()
    } else {
        // assume genomes is a pointer. find all .genome children and return array
        return $(genomes).find('.genome').map(function () {
            return $(this).text()
        }).get()
    }
}

let showOrganismClickMenu = function (event, organism = 'auto', species = 'auto', siblings = 'auto') {
    console.log('showTaxidClickMenu event:', event, 'organism', organism, 'siblings', siblings)
    // auto-discover species
    species = autoDiscoverSpecies(event, species)

    // auto-discover annotation
    organism = autoDiscoverSelf(event, organism)

    // auto-discover siblings (nothing to do with them yet)
    // siblings = autoDiscoverSiblings(event, taxname, siblings, 'organism')

    // initiate context menu
    let cm = new ClickMenu(event, 'organism-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" data-species="${species}">
${organism}</h6>
<a href="/organism/${organism}" class="dropdown-item context-menu-icon context-menu-icon-organism">
Open organism info</a>
`)

    cm.show()
}


let showGenomeClickMenu = function (event, genome = 'auto', species = 'auto', siblings = 'auto', annotations = 'auto') {
    console.log('showGenomeClickMenu', 'event:', event, 'genome:', genome, 'species:', species, 'siblings:', siblings, 'annotations', annotations)
    // auto-discover species
    species = autoDiscoverSpecies(event, species)

    // auto-discover genome
    genome = autoDiscoverSelf(event, genome)

    // auto-discover siblings
    siblings = autoDiscoverSiblings(event, genome, siblings, 'genome')

    // auto-discover annotations
    annotations = autoDiscoverSiblings(event, undefined, annotations, 'annotation')
    console.log(annotations)

    let cm = new ClickMenu(event, 'genome-context-menu')

    // list of elements to click on
    let html = `
<h6 class="dropdown-header context-menu-header" data-species="${species}">
${genome}</h6>`

    if (species) {
        html += `
<a href="/taxname/${species}" class="dropdown-item context-menu-icon context-menu-icon-taxid">
${species}</a>`
    }

    html += `
<a href="/genome/${genome}" class="dropdown-item context-menu-icon context-menu-icon-organism">
Open genome info</a>
<a onclick="CopyToClipboard('${genome}')" class="dropdown-item context-menu-icon context-menu-icon-copy">
Copy identifier</a>
<a href="/pathway/?genomes=${genome}" class="dropdown-item context-menu-icon context-menu-icon-pathway">
Open genome on pathway map</a>
<a href="/annotation-search/?genomes=${genome}" class="dropdown-item context-menu-icon context-menu-icon-annotation">
Search for annotations in genome</a>
<a href="/blast/?genomes=${genome}" class="dropdown-item context-menu-icon context-menu-icon-blast">
Blast genome</a>
`

    if (annotations.length > 0) {
        html += `
<h6 class="dropdown-header context-menu-header many-annotations">
${genome} and ${annotations.length} selected annotations</h6>
<a href="/annotation-search/?genomes=${genome}&annotations=${urlReplBlanks(annotations)}" class="dropdown-item context-menu-icon context-menu-icon-annotations many-annotations">
Perform annotation search</a>
</div>
`
    }

    if (siblings.length > 1) {
        const siblings_str = siblings.join('+')
        const siblings_str_comma = siblings.join(', ')
        console.log(siblings_str_comma)
        html += `
<h6 class="dropdown-header context-menu-header many-genomes">
${siblings.length} selected genomes</h6>
<a href="/trees/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-tree">
Show phylogenetic trees</a>
<a onclick="CopyToClipboard('${siblings_str_comma}')" class="dropdown-item many-genomes context-menu-icon context-menu-icon-copy">
Copy selected genomes</a>
<a href="/pathway/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-pathway">
Open genomes on pathway map</a>
<a href="/annotation-search/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-annotations">
Search for annotations in genomes</a>
<a href="/gene-trait-matching/?g1=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-gene-trait-matching">
Perform gene trait matching with these genomes as Group 1</a>
<a href="/blast/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-blast">
Blast genomes</a>
</div>
`
        if (annotations.length > 0) {
            html += `
<h6 class="dropdown-header context-menu-header many-annotations">
${siblings.length} genomes and ${annotations.length} selected annotations</h6>
<a href="/annotation-search/?genomes=${siblings_str}&annotations=${urlReplBlanks(annotations)}" class="dropdown-item context-menu-icon context-menu-icon-annotations many-annotations">
Perform annotation search</a>
</div>
`
        }
    }

    cm.appendElement(html)

    cm.show()
}

let showAnnotationClickMenu = function (event, annotation = 'auto', siblings = 'auto', genomes = 'none', annotype = 'auto') {
    console.log('showAnnotationClickMenu', 'event:', event, 'annotation:', annotation, 'siblings:', siblings, 'genomes', genomes, 'annotype', annotype)

    // auto-discover
    annotation = autoDiscoverSelf(event, annotation)
    siblings = autoDiscoverSiblings(event, annotation, siblings, 'annotation')
    let siblings_repl = urlReplBlanks(siblings)
    genomes = autoDiscoverGenomes(genomes)

    if (annotype === 'auto') {
        annotype = $(event.target).data('annotype')
    }

    let cm = new ClickMenu(event, 'annotation-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" data-annotype="${annotype}">
${annotation}</h6>
<a href="/annotation/${annotation}" class="dropdown-item context-menu-icon context-menu-icon-annotation">
Show details about this annotation</a>
<a onclick="CopyToClipboard('${annotation}')" class="dropdown-item context-menu-icon context-menu-icon-copy">
Copy annotation</a>
`)

    if (siblings.length > 1) {
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header many-annotations">
${siblings.length} selected annotations</h6>
<a href="/annotation-search/?annotations=${siblings_repl}" class="dropdown-item context-menu-icon context-menu-icon-annotations many-annotations">
Search for annotations</a>
</div>
`)
    }

    if (genomes.length > 0) {
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header many-genes">
${genomes.length} selected genomes</h6>
<a href="/compare-genes/?genomes=${genomes.join('+')}&annotations=${urlReplBlanks([annotation])}" class="dropdown-item context-menu-icon context-menu-icon-genes many-genes">
Compare the genes of this annotation</a>
</div>
`)
    }

    if (genomes.length > 1 && siblings.length > 1) {
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header many-genes">
${genomes.length} genomes and ${siblings.length} annotations</h6>
<a href="/compare-genes/?genomes=${genomes.join('+')}&annotations=${siblings_repl}" class="dropdown-item context-menu-icon context-menu-icon-genes many-genes">
Compare the genes of these annotations</a>
</div>
`)
    }

    cm.show()
}

let showGenesClickMenu = function (event, genes, species) {
    console.log('showGeneSClickMenu event:', event, 'genes', genes, 'species', species)
    // const genes = event.target.getAttribute('data-genes').split(separator)
    // console.log(genes)

    // initiate context menu
    let cm = new ClickMenu(event, 'genes-context-menu')

    let html = `
<h6 class="dropdown-header context-menu-header">
${genes.length} genes</h6>
<div class="read-only-div">`

    genes.forEach(gene => {
        console.log(gene)
        html += `<div class="gene ogb-tag" data-species="${species}" data-toggle="tooltip" onclick="showGeneClickMenu(event)">${gene}</div>`
    })

    html += `</div>`

    cm.appendElement(html)

    cm.show()
}

let showGeneClickMenu = function (event, gene = 'auto', siblings = 'auto') {
    console.log('showGeneClickMenu event:', event, 'gene', gene, 'siblings', siblings)

    // auto-discover annotation
    gene = autoDiscoverSelf(event, gene)

    // auto-discover siblings
    siblings = autoDiscoverSiblings(event, gene, siblings, 'gene')

    // initiate context menu
    let cm = new ClickMenu(event, 'gene-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 id='gene-context-menu-species-missing' class="dropdown-header context-menu-header">
${gene}</h6>
<h6 id='gene-context-menu-gene-product-missing' class="dropdown-header context-menu-header" hidden>
'hidden gene product name'</h6>
<a href="/gene/${gene}" class="dropdown-item context-menu-icon context-menu-icon-gene">
Open gene info</a>
`)

    if (siblings.length > 1) {
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header">
${siblings.length} selected genes</h6>
<a href="/compare-genes/?genes=${siblings.join('+')}" class="dropdown-item context-menu-icon context-menu-icon-annotations">
Compare genes</a>
</div>
`)
    }

    $.getJSON("/api/get-gene", {'gene_identifier': gene}, function (data) {
        let genome = data['genome']
        let taxid = data['taxid']
        let species = data['species']
        let annotype_to_gene = data['annotype_to_gene']

        if (annotype_to_gene['GP'] != undefined && annotype_to_gene['GP'][0]["name"] != undefined) {
            $('#gene-context-menu-gene-product-missing').text(annotype_to_gene['GP'][0]["name"]).removeAttr('hidden')
        }

        document.getElementById('gene-context-menu-species-missing').setAttribute('data-species', species)

        let html = `
<h6 class="dropdown-header context-menu-header" data-species="${species}" onclick="showGenomeClickMenu(event)">
${genome}</h6>
<a href="/genome/${genome}" class="dropdown-item context-menu-icon context-menu-icon-organism">
Open genome info</a>
<h6 class="dropdown-header context-menu-header">
Annotations</h6>
`
        for (const [anno_type, annotations] of Object.entries(annotype_to_gene)) {
            html += `
<div style="display: inline-flex">
    <div class="dropdown-item context-menu-icon context-menu-icon-annotations" data-annotype="${anno_type}">
    ${annotations[0]['anno_type_verbose']} (${annotations.length})</div>
    <div class="btn-group dropright">
    <button class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="font-size: 1rem; padding: 0rem 0.8rem">
    </button>
        <div class="dropdown-menu" style="width: 400px">`

            annotations.forEach(a => {
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
    })
    cm.show()
}

let showTaxidClickMenu = function (event, taxname = 'auto', siblings = 'auto') {
    console.log('showTaxidClickMenu event:', event, 'taxname', taxname, 'siblings', siblings)

    // auto-discover annotation
    taxname = autoDiscoverSelf(event, taxname)

    // auto-discover siblings (nothing to do with them yet)
    // siblings = autoDiscoverSiblings(event, taxname, siblings, 'taxid')

    // initiate context menu
    let cm = new ClickMenu(event, 'taxid-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" data-species="${taxname}">
${taxname}</h6>
<a href="/taxname/${taxname}" class="dropdown-item context-menu-icon context-menu-icon-taxid">
Open taxid info</a>
`)

    cm.show()
}

