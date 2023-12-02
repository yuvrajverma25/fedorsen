

document.getElementById("fedorsenText").addEventListener("click", function() {
    // Get the href from the data attribute
    var newHref = this.getAttribute("data-href");
    
    // Change the window location to the new href
    window.location.href = newHref;
});

document.addEventListener("DOMContentLoaded", function () {
    var tableRows = document.querySelectorAll("tbody tr[data-href]");
    tableRows.forEach(function (row) {
        row.addEventListener("click", function () {
            var hrefValue = row.getAttribute("data-href");
            window.open(hrefValue, '_blank');
        });
    });
});
