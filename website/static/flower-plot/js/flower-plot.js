let showAnnotationQueryClickMenu = function (event, genomes, notGenomes, annoType, description, nAnnos) {
    console.log('showAnnotationQueryClickMenu', 'event:', event, 'genomes:',
        genomes, 'notGenomes:', notGenomes, 'annoType', annoType, 'nAnnos', nAnnos)

    genomes = genomes.join(',')
    notGenomes = notGenomes.join(',')

    const isDisabled = nAnnos == 0 ? 'disabled' : ''
    console.log('isDisabled', isDisabled)
    console.log('nAnnos', nAnnos)

    let cm = new ClickMenu(event, 'annotation-context-menu')

    // list of elements to click on
    cm.appendElement(`
<h6 class="dropdown-header context-menu-header" data-annotype="${annoType}">
${description}</h6>
<a href="/annotations/?not_genomes=${notGenomes}&genomes=${genomes}&anno_type=${annoType}" 
class="dropdown-item context-menu-icon context-menu-icon-annotation ${isDisabled}">
Show list of annotations</a>
`)

    cm.show()
}
