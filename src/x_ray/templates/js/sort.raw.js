(function () {
    var ASC = "asc";
    var DESC = "desc";
    var SORTABLE = "data-sortable";
    var SORT_VALUE = "data-sort-value";
    var DIR_ATTR = "data-sort-dir";

    /**
     * Get the sort value for a cell: explicit data-sort-value span,
     * then fall back to the cell's visible text content.
     */
    function getSortValue(td) {
        var span = td.querySelector("span[" + SORT_VALUE + "]");
        if (span) {
            return span.getAttribute(SORT_VALUE);
        }
        return (td.textContent || "").trim();
    }

    /**
     * Compare two sort values, trying numeric comparison first,
     * then falling back to locale-aware string comparison.
     */
    function compareValues(a, b) {
        var na = Number(a), nb = Number(b);
        if (!isNaN(na) && !isNaN(nb)) {
            return na - nb;
        }
        return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: "base" });
    }

    /**
     * Sort the rows of a <tbody> by the values in column colIdx.
     */
    function sortTable(tbody, colIdx, dir) {
        var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
        rows.sort(function (a, b) {
            var cellA = a.children[colIdx];
            var cellB = b.children[colIdx];
            if (!cellA || !cellB) return 0;
            var cmp = compareValues(getSortValue(cellA), getSortValue(cellB));
            return dir === ASC ? cmp : -cmp;
        });
        rows.forEach(function (row) { tbody.appendChild(row); });
    }

    /**
     * Remove sort direction indicators from all headers in a table.
     */
    function clearSortIndicators(table) {
        var ths = table.querySelectorAll("thead th");
        for (var i = 0; i < ths.length; i++) {
            ths[i].removeAttribute(DIR_ATTR);
        }
    }

    /**
     * Update the header to show the current sort direction.
     */
    function setSortIndicator(th, dir) {
        clearSortIndicators(th.closest("table"));
        th.setAttribute(DIR_ATTR, dir);
    }

    /**
     * Handle a click on a sortable header cell.
     */
    function onHeaderClick(th) {
        var table = th.closest("table");
        var tbody = table.querySelector("tbody");
        if (!tbody) return;

        var row = th.parentNode;
        var colIdx = Array.prototype.indexOf.call(row.children, th);

        var currentDir = th.getAttribute(DIR_ATTR);
        var newDir = currentDir === ASC ? DESC : ASC;

        sortTable(tbody, colIdx, newDir);
        setSortIndicator(th, newDir);
    }

    // Attach click handlers to all sortable table headers.
    document.addEventListener("DOMContentLoaded", function () {
        var tables = document.querySelectorAll("table");
        for (var t = 0; t < tables.length; t++) {
            var table = tables[t];
            var ths = table.querySelectorAll("thead th span[" + SORTABLE + "]");
            if (ths.length === 0) continue;

            for (var h = 0; h < ths.length; h++) {
                var span = ths[h];
                if (span.getAttribute(SORTABLE) !== "true") continue;
                var th = span.parentNode;
                th.style.cursor = "pointer";
                th.addEventListener("click", function () {
                    onHeaderClick(this);
                });
            }
        }
    });
})();
