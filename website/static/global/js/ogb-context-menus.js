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

        // set z-index accordingly, starting at z-index 1031
        for (const [idx, menu_id] of Object.entries(contextMenuQueue)) {
            document.getElementById(menu_id).style.zIndex = 1031 + eval(idx)
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
                    preventOverflow: {
                        enabled: true,
                        boundariesElement: 'viewport',
                    },
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
        return siblings.find('.' + type).not('[data-annotype="fake"]').map(function () {
            return $(this).text()
        }).get()
    } else if (siblings === 'auto') {
        siblings = (self_string === undefined) ? [] : [self_string]
        $(event.target).siblings().each(function () {
            if ($(this).hasClass(type)) {
                siblings.push($(this).text())
            }
        })
    } else if (typeof (siblings) === 'string') {
        let target = siblings
        siblings = (self_string === undefined) ? [] : [self_string]
        $(target).find('.' + type).not('[data-annotype="fake"]').each(function () {
            siblings.push($(this).text())
        })
    } else {
        assert(Array.isArray(siblings), 'This function expects an array, a JQuery selector or nothing!!')
    }
    return removeDuplicates(siblings)
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
        return removeDuplicates(genomes)
    } else if (genomes instanceof jQuery) {
        return removeDuplicates(genomes.find('.genome').map(function () {
            return $(this).text()
        }).get())
    } else {
        // assume genomes is a pointer. find all .genome children and return array
        return removeDuplicates($(genomes).find('.genome').map(function () {
            return $(this).text()
        }).get())
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

    // warning tags
    let warningTags = event.target.classList.contains('restricted') ? '<span class="ogb-tag mini restricted float-right" data-title="restricted">r</span>' : ''

    // initiate context menu
    let cm = new ClickMenu(event, 'organism-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" data-species="${species}">
${organism}${warningTags}</h6>
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
    // remove fake annotations ([data-annotype="fake"])

    let cm = new ClickMenu(event, 'genome-context-menu')

    // warning tags
    let warningTags = '';
    ['restricted', 'no-representative', 'contaminated'].forEach(function (className) {
        if (event.target?.classList?.contains(className)) {
            warningTags += `<span class="ogb-tag mini ${className} float-right" data-title="${className}">${className.charAt(0)}</span>`
        }
    })

    // list of elements to click on
    let html = `
<h6 class="dropdown-header context-menu-header" data-species="${species}">
${genome}${warningTags}</h6>`

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
<a href="/pathway/?g1=${genome}" class="dropdown-item context-menu-icon context-menu-icon-pathway">
Open pathway map</a>
<a href="/annotation-search/?genomes=${genome}" class="dropdown-item context-menu-icon context-menu-icon-annotation">
Search for annotations</a>
<a href="/blast/?genomes=${genome}" class="dropdown-item context-menu-icon context-menu-icon-blast">
Blast</a>
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
        html += `
<h6 class="dropdown-header context-menu-header many-genomes">
${siblings.length} selected genomes</h6>
<a onclick="CopyToClipboard('${siblings_str_comma}')" class="dropdown-item many-genomes context-menu-icon context-menu-icon-copy">
Copy genome identifiers</a>`

        if (siblings.length === 2) {
            html += `
<a href="/dotplot/?ref=${siblings[0]}&query=${siblings[1]}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-dotplot">
Compare the assemblies using dotplot</a>
`
        }

        html += `
<a href="/trees/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-tree">
Show phylogenetic trees</a>
<a href="/pathway/?g1=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-pathway">
Open all on pathway map</a>
<a href="/annotation-search/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-annotations">
Search for annotations in all</a>
<a href="/flower-plot/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-flower-plot">
Show flower plot</a>
<a href="/gene-trait-matching/?g1=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-gene-trait-matching">
Perform gene trait matching</a>
<a href="/blast/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-blast">
Blast all</a>
<a href="/downloader/?genomes=${siblings_str}" class="dropdown-item many-genomes context-menu-icon context-menu-icon-downloader">
Open downloader</a>
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

    $('.ogb-tag.mini').tooltip()
}
/**
 * Generate a context menu for annotations
 *
 * @param event
 * @param annotation: single annotation (string)
 * @param siblings: other annotations ('auto' or array)
 * @param groupOfGenomes: dictionary: {genomeName -> arrayOfGenomes}
 * @param annotype: 'auto' or string
 */
let showAnnotationClickMenu = function (event, annotation = 'auto', siblings = 'auto', groupOfGenomes = {}, annotype = 'auto') {
    console.log('showAnnotationClickMenu', 'event:', event, 'annotation:', annotation, 'siblings:', siblings, 'groupOfGenomes', groupOfGenomes, 'annotype', annotype)

    // auto-discover
    annotation = autoDiscoverSelf(event, annotation)
    siblings = autoDiscoverSiblings(event, annotation, siblings, 'annotation')
    let siblings_repl = urlReplBlanks(siblings)
    groupOfGenomes = Object.entries(groupOfGenomes).reduce((newObj, [name, genomes]) => {
        newObj[name] = autoDiscoverGenomes(genomes)
        return newObj
    }, {})

    let description = ''
    for (var attr of ['data-original-title', 'title']) {
        const val = event.target.getAttribute(attr)
        if (typeof val === 'string' && val.length > 0) {
            description = `
<h6 class="dropdown-header context-menu-header">
${val}</h6>
`
            break
        }
    }

    if (annotype === 'auto') {
        annotype = $(event.target).data('annotype')
    }

    let cm = new ClickMenu(event, 'annotation-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" data-annotype="${annotype}">
${annotation}</h6>
${description}
<a href="/annotation/${annotation}" class="dropdown-item context-menu-icon context-menu-icon-annotation">
Show details about this annotation</a>
<a onclick="CopyToClipboard('${annotation}')" class="dropdown-item context-menu-icon context-menu-icon-copy">
Copy annotation</a>
`)

    // show hyperlinks
    let hyperlinks
    try {
        hyperlinks = annotationsJson[annotype]['hyperlinks']
    } catch (e) {
        console.log('showAnnotationClickMenu: Failed to read hyperlinks for', annotype, annotation)
        hyperlinks = []
    }
    hyperlinks.forEach(function (data) {
        const name = data['name']
        console.log('`' + data['url'] + '`', eval('`' + data['url'] + '`'))
        const url = eval('`' + data['url'] + '`')
        cm.appendElement(`<a href="${url}" class="dropdown-item context-menu-icon context-menu-icon-hyperlink">${name}</a>`)
    })

    // Compare genes
    Object.entries(groupOfGenomes).forEach(([name, genomes]) => {
        // for each group of genomes
        name = (name === '') ? '' : `${name}: `
        console.log('loop', name, genomes)
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header many-genes">
${name}${genomes.length} genomes</h6>

<a href="/compare-genes/?genomes=${genomes.join('+')}&annotations=${urlReplBlanks([annotation])}" class="dropdown-item context-menu-icon context-menu-icon-genes many-genes">
Compare the genes</a>
</div>
`)
    })

    // Annotation search with genomes
    Object.entries(groupOfGenomes).forEach(([name, genomes]) => {
        name = (name === '') ? '' : `${name}: `
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header many-annotations">
${name}${genomes.length} genomes and ${siblings.length} annotations</h6>

<a href="/annotation-search/?annotations=${siblings_repl}&genomes=${genomes.join('+')}&annotations=${siblings_repl}" class="dropdown-item context-menu-icon context-menu-icon-annotations many-annotations">
Search for annotations</a>
</div>
`)
    })

    // if other annotations
    if (siblings.length > 1) {
        cm.appendElement(`
<h6 class="dropdown-header context-menu-header many-genomes">
${siblings.length} selected annotations</h6>
<a onclick="CopyToClipboard('${siblings}')" class="dropdown-item many-genomes context-menu-icon context-menu-icon-copy">
Copy annotations</a>
`)
        // Annotation search without genomes
        if (Object.keys(groupOfGenomes).length === 0) {
            cm.appendElement(`
<a href="/annotation-search/?annotations=${siblings_repl}" class="dropdown-item context-menu-icon context-menu-icon-annotations many-genomes">
Search for annotations</a>
`)
        }
        cm.appendElement('</div>')
    }

    $.post('/api/get-annotation/', {'annotation_name': annotation}, function (data) {
        const pathways = data['pathways']
        let html = ''

        // Pathways
        if (pathways.length) {
            html += `
<h6 class="dropdown-header context-menu-header">
Pathways</h6>
<div style="display: inline-flex">
    <div class="dropdown-item context-menu-icon context-menu-icon-pathway">
    This annotation occurs on ${pathways.length} pathways</div>
    <div class="btn-group dropright">
    <button class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="font-size: 1rem; padding: 0rem 0.8rem">
    </button>
        <div class="dropdown-menu no-collapse" style="width: 400px">`

            pathways.forEach(p => {
                html += `
<p class="dropdown-item" onclick="event.stopPropagation()">
<span class="ogb-tag pathway" title="${p[1]}" onclick="showPathwayClickMenu(event)">${p[0]}</span>:
${p[1]}`
            })

            html += `
        </div>
    </div>
</div>`
        }


        cm.appendElement(html)
        cm.popper.update()
    }, "json")

    cm.show()
}

let showGenesClickMenu = function (event, genes, species) {
    console.log('showGeneSClickMenu event:', event, 'genes', genes, 'species', species)

    // initiate context menu
    let cm = new ClickMenu(event, 'genes-context-menu')

    let html = `
<h6 class="dropdown-header context-menu-header">
${genes.length} genes</h6>
<div class="read-only-div">`

    genes.forEach(gene => {
        html += `<div class="gene ogb-tag" data-species="${species}" onclick="showGeneClickMenu(event)">${gene}</div>`
    })

    html += `</div>`

    cm.appendElement(html)

    cm.show()

    $('#' + cm.menu_id).find('.gene').ogbTooltip()
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

    $.post('/api/get-gene/', {'gene_identifier': gene}, function (data) {
        const genome = data['genome']
        const taxid = data['taxid']
        const species = data['species']
        const annotype_to_gene = data['annotype_to_gene']
        const pathways = data['pathways']

        if (annotype_to_gene['GP'] != undefined && annotype_to_gene['GP'][0]["name"] != undefined) {
            $('#gene-context-menu-gene-product-missing').text(annotype_to_gene['GP'][0]["name"]).removeAttr('hidden')
        }

        document.getElementById('gene-context-menu-species-missing').setAttribute('data-species', species)

        let html = `
<h6 class="dropdown-header context-menu-header" data-species="${species}" onclick="showGenomeClickMenu(event)">
${genome}</h6>
<a href="/genome/${genome}" class="dropdown-item context-menu-icon context-menu-icon-organism">
Open genome info</a>
`

        // Pathways
        if (pathways.length) {
            html += `
<h6 class="dropdown-header context-menu-header">
Pathways</h6>
<div style="display: inline-flex">
    <div class="dropdown-item context-menu-icon context-menu-icon-pathway">
    This gene occurs on ${pathways.length} pathways</div>
    <div class="btn-group dropright">
    <button class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="font-size: 1rem; padding: 0rem 0.8rem">
    </button>
        <div class="dropdown-menu no-collapse" style="width: 400px">`

            pathways.forEach(p => {
                html += `
<p class="dropdown-item" onclick="event.stopPropagation()">
<span class="ogb-tag pathway" title="${p[1]}" onclick="showPathwayClickMenu(event, ['${genome}'])">${p[0]}</span>:
${p[1]}`
            })

            html += `
        </div>
    </div>
</div>`
        }

        // Annotations
        if (Object.keys(annotype_to_gene).length) {
            html += `
<h6 class="dropdown-header context-menu-header">
Annotations</h6>`
        }
        for (const [anno_type, annotations] of Object.entries(annotype_to_gene)) {
            html += `
<div style="display: inline-flex">
    <div class="dropdown-item context-menu-icon context-menu-icon-annotations" data-annotype="${anno_type}">
    ${annotations[0]['anno_type_verbose']} (${annotations.length})</div>
    <div class="btn-group dropright">
    <button class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="font-size: 1rem; padding: 0rem 0.8rem">
    </button>
        <div class="dropdown-menu no-collapse" style="width: 400px">
`

            annotations.forEach(a => {
                html += `
<p class="dropdown-item" onclick="event.stopPropagation()">
    <span class="ogb-tag annotation" data-annotype="${anno_type}" title="${a.description}" 
        onclick="showAnnotationClickMenu(event)"
        >${a.name}</span>: ${a.description || 'no description'}
<\p>`
            })

            html += `
        </div>
    </div>
</div>`
        }
        cm.appendElement(html)
        cm.popper.update()
    }, "json")

    cm.show()
}

let showTaxidClickMenu = function (event, taxname = 'auto', taxRank = 'auto') {
    console.log('showTaxidClickMenu event:', event, 'taxname', taxname, 'taxRank', taxRank)

    // auto-discover taxname
    taxname = autoDiscoverSelf(event, taxname)

    const selector = `@${taxRank === 'auto' ? 'tax' : taxRank}:${taxname}`

    const genomeTablesLink = `/genomes/?columns=organism,identifier,taxonomy,taxid,taxsuperkingdom,taxphylum,taxclass,taxorder,taxfamily,taxgenus,taxspecies,taxsubspecies&${taxRank === 'auto' ? 'taxonomy' : taxRank}=${taxname}`

    // initiate context menu
    let cm = new ClickMenu(event, 'taxid-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" data-species="${taxname}">
${taxname}</h6>
<a href="/taxname/${taxname}" class="dropdown-item context-menu-icon context-menu-icon-taxid">
Open taxid info</a>
<a href="${genomeTablesLink}" class="dropdown-item context-menu-icon context-menu-icon-table">
Show genomes</a>
<a onclick="CopyToClipboard('${selector}')" class="dropdown-item context-menu-icon context-menu-icon-copy">
Copy selector (${selector})</a>
`)

    cm.show()
}


let autoDiscoverDescription = function (event) {
    for (const attr of ['description', 'title', 'original-title']) {
        const description = $(event.target).data(attr)
        if (description && description.length) {
            return description
        }
    }
    return '-'
}


let showTagClickMenu = function (event, tag = 'auto', description = 'auto') {
    console.log('showTagClickMenu event:', event, 'tag', tag, 'description', description)

    // auto-discover tag
    tag = autoDiscoverSelf(event, tag)

    const backgroundColor = $(event.target).css('background-color')
    const textColor = $(event.target).css('color')

    // auto-discover description (nothing to do with them yet)
    description = autoDiscoverDescription(event)

    // initiate context menu
    let cm = new ClickMenu(event, 'tag-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" style="color:${textColor}; background-color: ${backgroundColor}">
${tag}</h6>
<h6 class="dropdown-header context-menu-header">
${description}</h6>
<a onclick="CopyToClipboard('@tag:${tag}')" class="dropdown-item context-menu-icon context-menu-icon-copy">
Copy selector (@tag:${tag})</a>
`)

    cm.show()
}


let showPathwayClickMenu = function (event, genomes = 'none') {
    console.log('showTagClickMenu event:', event, 'genome', genomes)

    // auto-discover genomes
    genomes = autoDiscoverGenomes(genomes)

    const slug = event.target.textContent
    const title = event.target?.getAttribute('title') || event?.target?.getAttribute('data-original-title') || '-'
    const backgroundColor = $(event.target).css('background-color')
    const textColor = $(event.target).css('color')

    const genomeUrlString = genomes.length ? '&g1=' + genomes.join(',') : ''

    // initiate context menu
    let cm = new ClickMenu(event, 'pathway-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" style="color:${textColor}; background-color: ${backgroundColor}">
${slug}</h6>
<h6 class="dropdown-header context-menu-header">
${title}</h6>
<a href="/pathway/?map=${slug}${genomeUrlString}" class="dropdown-item context-menu-icon context-menu-icon-pathway">
Open pathway map</a>
<a href="/annotations/?pathway_map=${slug}" class="dropdown-item context-menu-icon context-menu-icon-annotations">
See annotations behind pathway map</a>
`)

    cm.show()

}

