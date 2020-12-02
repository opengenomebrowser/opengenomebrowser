/* Set the width of the side navigation to 500px */
sidebarlisterner_running = false

function openNav(event) {

    event.stopPropagation()

    document.getElementById("ogbSidenav").style.width = "500px";

    // add listener to close the menu
    if (!sidebarlisterner_running) {
        $(document).on('click', function (e) {
            if (e.altKey || e.metaKey || $('#ogbSidenav').has(e.target).length == 1 || $('#ogbSidenav').is(e.target)) {
                // ignore clicks with alt or meta keys
                // ignore clicks on dropdown
            } else {
                // hide div
                closeNav(event)
            }
        });
        sidebarlisterner_running = true
    }

}

/* Set the width of the side navigation to 0 */
function closeNav(event) {
    document.getElementById("ogbSidenav").style.width = "0"
}

/* Toggle Navbar */
function toggleNav(event) {
    var side_bar_state = document.getElementById("ogbSidenav").style.width

    if (side_bar_state == "" || side_bar_state == "0px") {
        openNav(event);
    } else {
        closeNav(event);
    }
}
