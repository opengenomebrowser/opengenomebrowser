/* Set the width of the side navigation to 500px */
function openNav() {
    document.getElementById("mySidenav").style.width = "500px";
}

/* Set the width of the side navigation to 0 */
function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}

/* Toggle */
function toggleNav() {
    var side_bar_state = document.getElementById("mySidenav").style.width;
    if (side_bar_state == "" || side_bar_state == "0px") {
        openNav();
    } else {
        closeNav();
    }
}