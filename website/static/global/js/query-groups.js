"use strict"

let randomGenomeGroupIncrement = 100  // ensure unique IDs

function addGenomesGroup(target, genomes = [], deleteButton = true, groupId = true) {
    const uniqueId = `get-genomes-${randomGenomeGroupIncrement += 1}`
    const currentGroupId = $('#query-genomes .group-count').length + 1

    if (deleteButton) {
        deleteButton = `
            <button onclick="removeGenomesQuery(event.target.parentElement)" type="button" class="btn-sm btn-danger float-right" title=""
                data-original-title="Delete group">Delete
            </button>`
    } else {
        deleteButton = ''
    }

    if (groupId) {
        groupId = ` (group <a class='group-count'>${currentGroupId}<a/>)`
    } else {
        groupId = ''
    }

    const el = `
        <div class="form-group get-genomes">
            <label for="${uniqueId}">Genomes${groupId}:</label>
            ${deleteButton}
            <button onclick="wipeQuery(event.target.parentElement)" type="button" class="btn-sm btn-warning float-right" title=""
                data-original-title="Wipe content">Wipe
            </button>
            <button onclick="copyQuery(event.target.parentElement)" type="button" class="btn-sm btn-info float-right" title=""
                data-original-title="Copy content">Copy
            </button>
            <input type="text" class="form-control" id="${uniqueId}"
               value="${genomes.join(',')}">
        </div>
        `
    target.append(el)
    init_autocomplete_genomes('#' + uniqueId)
}

function removeGenomesQuery(target) {
    $(target).closest('.get-genomes').remove()
    $('#query-genomes .group-count').each(function (i, element) {
        element.text = i + 1
    })
}

function extractQuery(target) {
    return $(target).find('.tag-editor').text()
        .replace(/\s*,\s*/g, ",")  // remove all whitespace around commas
        .replace(/^,/, "")  // remove leading comma
        .split(",")  // split into list of identifiers/magic strings
}

function copyQuery(target) {
    CopyToClipboard(extractQuery(target).join(', '))
}

function wipeQuery(target) {
    $(target).find('.tag-editor').text('')
}
