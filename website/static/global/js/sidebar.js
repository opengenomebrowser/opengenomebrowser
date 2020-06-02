/* Set the width of the side navigation to 500px */
function openNav(event) {

    event.stopPropagation()

    document.getElementById("mySidenav").style.width = "500px";

    // add listener to close the menu
    $(document).on('click', function (e) {
        if (e.altKey || e.metaKey || $('#mySidenav').has(e.target).length == 1 || $('#mySidenav').is(e.target)) {
            // ignore clicks with alt or meta keys
            // ignore clicks on dropdown
        } else {
            // hide div
            closeNav(event)
            // destroy listener
            $(this).off('click')
        }
    });

}

/* Set the width of the side navigation to 0 */
function closeNav(event) {
    document.getElementById("mySidenav").style.width = "0"
}

/* Toggle */
function toggleNav(event) {
    var side_bar_state = document.getElementById("mySidenav").style.width

    if (side_bar_state == "" || side_bar_state == "0px") {
        openNav(event);
    } else {
        closeNav(event);
    }
}