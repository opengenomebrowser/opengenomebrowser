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
 * @param {Element} element Element to be saved
 * @param {String} filename default: download.png
 */
function savePng(element, filename = 'download.png') {
    $(window).scrollTop(0)  // otherwise, png will be cropped.
    html2canvas(element).then(function (canvas) {
        saveUriAs(canvas.toDataURL(), filename)
    })
}

/**
 * Save a map as svg, opens save-as dialog
 *
 * @param {Element} element SVG element to be saved
 * @param {String} filename default: download.png
 */
function saveSvg(element, filename = 'download.svg') {
    //serialize svg.
    let serializer = new XMLSerializer()
    let data = serializer.serializeToString(element)

    data = encodeURIComponent(data)

    // add file type declaration
    data = 'data:image/svg+xml;charset=utf-8,' + data

    saveUriAs(data, filename)
}
