"use strict"


jQuery.fn.extend({
    ogbTooltip: function () {
        this.each(function () {
            if (jQuery._data(this, 'events') !== undefined) {
                console.log('do not append multiple events!')
                return  // ensure not two events are appended
            }
            if (this.matches('.genome') || this.matches('.gene') || this.matches('.taxid') || this.matches('.organism')) {
                $(this).tooltip({
                    boundary: 'window',
                    title: function () {
                        return $(this).attr('data-species')
                    }
                })
            } else {
                $(this).tooltip({
                    boundary: 'window',
                })
            }
        })
        return this
    },
})

/**
 * Read and write cookies
 *
 * https://stackoverflow.com/questions/11344531/pure-javascript-store-object-in-cookie/11344672
 */
function writeCookie(name, value, expires_minutes = 120) {
    let expires = new Date()
    expires.setTime(expires.getTime() + (expires_minutes * 60 * 1000))

    let cookie = `${name}=${JSON.stringify(value)}; expires=${expires.toGMTString()}; path=/;  SameSite=Lax;`
    if (!window.location.host.startsWith('127.0.0.1')) {
        // cannot save cookies to localhost
        cookie += ` domain=.${window.location.host.toString()};`
    }
    document.cookie = cookie
}

function readCookie(name) {
    let result = document.cookie.match(new RegExp(name + '=([^;]+)'))
    result && (result = JSON.parse(result[1]))
    return result
}

function deleteCookie(name) {
    let cookie = `${name}=; expires=Thu, 01-Jan-1970 00:00:01 GMT; path=/; SameSite=Lax;`
    if (!window.location.host.startsWith('127.0.0.1')) {
        // cannot save cookies to localhost
        cookie += ` domain=.${window.location.host.toString()};`
    }
    document.cookie = cookie
}

let postRequestsOnly = false  // forwarding to new pages using POST requests (used for debugging only)

function goToPageWithData(location, data) {
    assert(location.substr(-1) !== '/', 'BAD URL in goToPageWithData: must NOT end in /')
    const url = calcUrl(location, data)
    const urlSize = (new TextEncoder().encode(url)).length
    console.log(postRequestsOnly, url, urlSize, data)
    if (postRequestsOnly || urlSize > 32000) {
        console.log('forward to new URL (POST request)')
        redirect(`${location}/?postrequest=true`, data)
    } else {
        console.log('forward to new URL (GET request)')
        window.location.href = url
    }

}

const alertModal = function (type, header, body) {
    const types = ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']

    const modal = $(`
<div class="modal fade" id="alertModal" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-header alert">
                <h5 class="modal-title" id="exampleModalLongTitle">Modal title</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">Modal message</div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>`)
    const modalHeader = modal.find('.modal-header')
    const modalTitle = modal.find('.modal-title')
    const modalBody = modal.find('.modal-body')

    assert(types.includes(type), `Type ${type} is not included in ${types}!`)

    modalHeader.removeClass(types.map(function (t) {
        return 'alert-' + t
    }))
    modalHeader.addClass('alert-' + type)

    modalTitle.text(header)
    modalBody.html(body)
    modal.modal('show')
}

function redirect(location, data, target = '_self') {
    let form = ''
    $.each(data, function (key, value) {
        form += `<input type="hidden" name="${key}" value="${postReplBlanks(value)}">`
    })
    $(`<form action="${location}" method="POST" target="${target}">
        <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
        ${form}
    </form>`).appendTo($(document.body)).submit()
}

function calcUrl(location, data) {
    let components = []
    for (const [key, value] of Object.entries(data)) {
        components.push(`${key}=${urlReplBlanks(value)}`)
    }
    return `${location}?${components.join('&')}`
}


/**
 * Read annotations.json from cookie
 */
let annotationsJson
jQuery(document).ready(function () {
    annotationsJson = readCookie('annotationsJson')
    if (annotationsJson === null) {
        $.getJSON("/files_html/annotations.json", function (data) {
            console.log('reload annotationsJson!')
            annotationsJson = data
            writeCookie('annotationsJson', data, 120)
        })
    }
})

/**
 * Toggle the taxonomy-stylesheet.
 */
function toggleColorizeTax() {
    let colorize_tax_checkbox = document.getElementById('colorize-tax-checkbox')
    let taxid_color_stylesheet = document.getElementById('taxid-color-stylesheet')

    taxid_color_stylesheet.disabled = !colorize_tax_checkbox.checked
}

/**
 * Toggle the sequence-viewer-stylesheet.
 */
function toggleColorizeSequence() {
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

/*
* Give or take 'is-invalid' class depending on test.
*/
const toggleValid = function (test, target) {
    if (test) {
        target.removeClass('is-invalid')
    } else {
        target.addClass('is-invalid')
    }

}


const assert = function (condition, message) {
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
    let split = this.split(sep)
    return maxsplit ? [split.slice(0, -maxsplit).join(sep)].concat(split.slice(-maxsplit)) : split
}

/*
 * Encode blanks as !!!, join array with +
 * E.g. ['OG0000006', 'OG0000010S24', 'S24 family peptidase']
 * becomes "OG0000006+OG0000010S24+S24!!!family!!!peptidase"
 */
let urlReplBlanks = function (input) {
    if ($.isArray(input)) {
        const encode = function (str) {
            return encodeURIComponent(String(str).replaceAll(' ', '!!!'))
        }
        return input.map(str => encode(str)).join('+')
    } else {
        return encodeURIComponent(String(input).replaceAll(' ', '!!!'))
    }
}
let postReplBlanks = function (input) {
    if ($.isArray(input)) {
        let encode = function (str) {
            return str.replaceAll(' ', '!!!')
        }
        return input.map(str => encode(str)).join(' ')
    } else {
        return input.replaceAll(' ', '!!!')
    }
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
 * Removes duplicate elements from array
 *
 * Usage:
 * removeDuplicates([1,1,1,2])
 * returns: [1, 2]
 */
const removeDuplicates = (array) => {
    return Array.from(new Set(array));
};


/*
 * Execute callback function when element changes
 *
 * Usage:
 * onChangeElement(selector, function() {
 *    // work the magic
 * })
 */
const onChangeElement = (selector, callback) => {
    const targetNode = document.querySelector(selector);
    if (targetNode) {
        // Options for the observer (which mutations to observe)
        const config = {attributes: true, childList: true, subtree: true};

        // Create an observer instance linked to the callback function
        const observer = new MutationObserver(callback);

        // Start observing the target node for configured mutations
        observer.observe(targetNode, config);
    } else {
        console.error("onChangeElement: Invalid Selector")
    }
}


/*
* Takes decimal like 0.2222 and returns 22.2  (rounded to one decimal)
*/
let formatPercent = function (relative) {
    return Math.round(relative * 1000) / 10
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

function validateGenomes(genomes) {
    return $.post('/api/validate-genomes/', {'genomes': genomes}, function (data) {
    }, "json")
}

function getGenomeIdentifiers(genomes) {
    return $.post('/api/validate-genomes/', {'genomes': genomes, 'get_identifiers': true}, function (data) {
    }, "json")
}

function validateGenes(genes) {
    return $.post('/api/validate-genes/', {'genes': genes}, function (data) {
    }, "json")
}

function validatePathwaymap(slug) {
    return $.post('/api/validate-pathwaymap/', {'slug': slug}, function (data) {
    }, "json")
}

function validateAnnotations(annotations) {
    return $.post('/api/validate-annotations/', {'annotations': annotations}, function (data) {
    }, "json")
}

function createReadOnlyGenomeDiv(genomeArray, genomeToVisualization, additionalClasses = '', clickMenuAnnotations = 'auto') {
    let readOnlyDiv = $('<div>', {
        class: "read-only-div " + additionalClasses,
        onclick: `CopyToClipboard('${genomeArray.join(', ')}')`
    })

    for (const genome of genomeArray) {
        if (!(genome in genomeToVisualization)) {
            console.log(genome, 'not in genomeToVisualization!')
        }
        const dataGenome = genomeToVisualization[genome]
        let classes = ['genome', 'ogb-tag']
        if (dataGenome['restricted']) classes.push('restricted')
        if (dataGenome['no_representative']) classes.push('no-representative')
        if (dataGenome['contaminated']) classes.push('contaminated')

        readOnlyDiv.append($('<span>', {
            text: genome,
            class: classes.join(' '),
            onclick: `showGenomeClickMenu(event, 'auto', 'auto', 'auto', '${clickMenuAnnotations}')`,
            'data-species': dataGenome['sciname'],
        }).ogbTooltip())
    }

    return readOnlyDiv
}

function initAutocompleteAnnotations(div_name) {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-annotations/',
            minLength: 1
        },
        placeholder: placeholders.annotation || '',
        delimiter: ',;',
        forceLowercase: false,
        onChange: onAnnotationsChange
    })

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0]
    onAnnotationsChange(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)

    // fix bug: sometimes, after pasting data, the on_change event was not triggered
    $(tag_editor_objects.editor).bind("paste", function (e) {
        setTimeout(function () {
            let tag_editor_objects = $(div_name).tagEditor('getTags')[0]
            onAnnotationsChange(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)
        }, 100)
    })
}

function onAnnotationsChange(field, editor, tags) {
    $.ajax({
        dataType: "json",
        url: '/api/annotation-to-type/',
        method: 'post',
        data: {'annotations[]': tags},
        success: function (data) {
            let entries = $('li', editor)

            entries.each(function () {
                let li = $(this)
                let child_1 = li.children()[1]
                let child_2 = li.children()[2]

                let anno = li[0].innerText.substring(3)

                if (anno in data) {
                    let annoData = data[anno]

                    child_1.setAttribute('data-annotype', annoData['anno_type'])
                    child_1.setAttribute('title', data[anno]['description'])
                    child_2.setAttribute('data-annotype', annoData['anno_type'])

                    child_1.classList.add('annotation')
                    $(child_1).tooltip()
                }
            })
        }
    })
}

function initAutocompleteGenomes(div_name, maxTags, placeholder = '') {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-genomes/',
            minLength: 1
        },
        delimiter: ',;',
        placeholder: placeholders.genome || '',
        forceLowercase: false,
        maxTags: maxTags ? maxTags : null,
        onChange: onGenomesChange
    })

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0]
    onGenomesChange(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)

    // fix bug: sometimes, after pasting data, the on_change event was not triggered
    $(tag_editor_objects.editor).bind("paste", function (e) {
        setTimeout(function () {
            let tag_editor_objects = $(div_name).tagEditor('getTags')[0]
            onGenomesChange(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)
        }, 100)
    })
}

function onGenomesChange(field, editor, tags) {
    $.ajax({
        dataType: "json",
        url: '/api/genome-identifier-to-species/',
        method: 'post',
        data: {'genomes[]': tags},
        success: function (data) {
            delete data.success

            let entries = $('li', editor)

            entries.each(function () {
                let li = $(this)
                let child_1 = li.children()[1]
                let child_2 = li.children()[2]

                let genome = li[0].innerText.substring(3)

                if (genome in data) {
                    let genome_data = data[genome]

                    if (genome_data['restricted']) child_1.classList.add('restricted')
                    if (genome_data['no_representative']) child_1.classList.add('no-representative')
                    if (genome_data['contaminated']) child_1.classList.add('contaminated')


                    if (genome_data['type'] === 'taxid' || genome_data['type'] === 'genome') {
                        child_1.setAttribute('data-species', genome_data['sciname'])
                        child_2.setAttribute('data-species', genome_data['sciname'])
                    } else if (genome_data['type'] === 'tag') {
                        child_1.setAttribute('data-tag', genome_data['tag'])
                        child_2.setAttribute('data-tag', genome_data['tag'])
                    } else {
                        console.log('ERROR in onGenomesChange!', genome, genome_data, li)
                    }

                    child_1.classList.add('genome')
                    $(child_1).ogbTooltip()
                }
            })
        }
    })
}

function initAutocompleteGenes(div_name) {
    // https://goodies.pixabay.com/jquery/tag-editor/demo.html
    $(div_name).tagEditor({
        autocomplete: {
            source: '/api/autocomplete-genes/',
            minLength: 1
        },
        placeholder: placeholders.gene || '',
        delimiter: ',; ',
        forceLowercase: false,
        onChange: onGenesChange
    })

    let tag_editor_objects = $(div_name).tagEditor('getTags')[0]

    onGenesChange(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)

    // fix bug: sometimes, after pasting data, the on_change event was not triggered
    $(tag_editor_objects.editor).bind("paste", function (e) {
        setTimeout(function () {
            let tag_editor_objects = $(div_name).tagEditor('getTags')[0]
            onGenesChange(tag_editor_objects.field, tag_editor_objects.editor, tag_editor_objects.tags)
        }, 100)
    })
}

function onGenesChange(field, editor, tags) {
    const genomes = Array.from(new Set(tags.map(function (gene) {
        return gene.rsplit('_', 1)[0]
    })))

    $.ajax({
        dataType: "json",
        url: '/api/genome-identifier-to-species/',
        method: 'post',
        data: {'genomes[]': genomes},
        success: function (data) {
            delete data.success

            let entries = $('li', editor)

            entries.each(function () {
                let li = $(this)
                let child_1 = li.children()[1]
                let child_2 = li.children()[2]

                const gene = li[0].innerText.substring(3)
                const genome = gene.rsplit('_', 1)[0]

                if (genome in data) {
                    child_1.setAttribute('data-species', data[genome]['sciname'])
                    child_2.setAttribute('data-species', data[genome]['sciname'])

                    child_1.classList.add('gene')
                    $(child_1).ogbTooltip()
                }
            })
        }
    })
}


const tableToTsv = function (tableElement, fileName) {
    let tsv = 'data:text/csv;charset=utf-8,'

    const header = $(tableElement).find('thead tr th').toArray().map(x => x.innerText.replace('#', 'Nr').split('\n').at(-1))
    tsv += header.join('\t')
    tsv += '\r\n'

    const rows = document.querySelectorAll('table tbody tr')
    for (const row of rows) {
        const rowData = []
        for (const [index, column] of row.querySelectorAll('th, td').entries()) {
            rowData.push(column.innerText)
        }
        tsv += rowData.join('\t')
        tsv += '\r\n'
    }

    saveUriAs(encodeURI(tsv), fileName)
}

const tableJsonListToTsv = function (tableElement, attribute, fileName) {
    let tsv = 'data:text/csv;charset=utf-8,'

    const header = $(tableElement).find('thead tr th').toArray().map(x => x.innerText.replace('#', 'Nr').split('\n').at(-1))
    tsv += header.join('\t')
    tsv += '\r\n'

    const rows = document.querySelectorAll('table tbody tr')
    for (const row of rows) {
        const rowData = []
        for (const [index, column] of row.querySelectorAll('th, td').entries()) {
            if (index === 0) {
                rowData.push(column.innerText)
            } else {
                rowData.push(JSON.parse(column.firstChild.getAttribute(attribute)).join(','))
            }
        }
        tsv += rowData.join('\t')
        tsv += '\r\n'
    }

    saveUriAs(encodeURI(tsv), fileName)
}
