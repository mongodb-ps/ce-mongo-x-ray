/*
 * Shared table copy-to-clipboard feature.
 * Renders a "Copy" button above every <table> that copies structured data
 * (plaintext tab-separated + formatted HTML) suitable for Google Docs paste.
 */

function tableText(table) {
    return Array.from(table.rows).map(function (row) {
        return Array.from(row.cells).map(function (cell) {
            return cell.innerText.replace(/\t/g, " ").trim();
        }).join("\t");
    }).join("\n");
}

function tableForClipboard(table) {
    var clone = table.cloneNode(true);
    var landscapeWidth = 864;
    var chartColumnWidth = 55;
    var maxImageWidth = 450;
    clone.setAttribute("width", String(landscapeWidth));
    clone.style.width = "9in";
    clone.style.maxWidth = "9in";
    clone.style.tableLayout = "fixed";
    clone.style.borderCollapse = "collapse";
    clone.querySelectorAll("th, td").forEach(function (cell) {
        cell.style.overflowWrap = "anywhere";
        cell.style.verticalAlign = "top";
        cell.style.border = "1px solid black";
    });
    if (clone.querySelector("img")) {
        Array.from(clone.rows).forEach(function (row) {
            var cells = Array.from(row.cells);
            if (!cells.length) return;
            var otherColumnWidth = (100 - chartColumnWidth) / Math.max(1, cells.length - 1);
            cells.forEach(function (cell, index) {
                var width = index === cells.length - 1 ? chartColumnWidth : otherColumnWidth;
                cell.setAttribute("width", width + "%");
                cell.style.width = width + "%";
            });
        });
    }
    clone.querySelectorAll("img").forEach(function (image) {
        var sourceWidth = Number(image.getAttribute("width")) || image.naturalWidth || maxImageWidth;
        var sourceHeight = Number(image.getAttribute("height")) || image.naturalHeight;
        var width = Math.min(sourceWidth, maxImageWidth);
        image.setAttribute("width", String(Math.round(width)));
        if (sourceHeight) {
            image.setAttribute("height", String(Math.round(sourceHeight * width / sourceWidth)));
        } else {
            image.removeAttribute("height");
        }
        image.style.display = "block";
        image.style.width = width + "px";
        image.style.maxWidth = "100%";
        image.style.height = "auto";
        image.style.objectFit = "contain";
    });
    return clone;
}

function copyTableSelection(table) {
    var selection = window.getSelection();
    if (!selection) return false;
    var container = document.createElement("div");
    container.style.position = "fixed";
    container.style.left = "-10000px";
    container.style.top = "0";
    container.style.width = "9in";
    container.appendChild(table);
    document.body.appendChild(container);
    var previousRanges = [];
    for (var index = 0; index < selection.rangeCount; index++) {
        previousRanges.push(selection.getRangeAt(index));
    }
    var range = document.createRange();
    range.selectNode(table);
    selection.removeAllRanges();
    selection.addRange(range);
    var copied = false;
    try {
        copied = document.execCommand("copy");
    } finally {
        selection.removeAllRanges();
        container.remove();
        previousRanges.forEach(function (previousRange) { selection.addRange(previousRange); });
    }
    return copied;
}

async function copyTable(table) {
    var clipboardTable = tableForClipboard(table);
    var html = clipboardTable.outerHTML;
    var text = tableText(table);
    if (navigator.clipboard && window.ClipboardItem && window.isSecureContext) {
        try {
            await navigator.clipboard.write([
                new ClipboardItem({
                    "text/html": new Blob([html], { type: "text/html" }),
                    "text/plain": new Blob([text], { type: "text/plain" })
                })
            ]);
            return true;
        } catch (error) {
            // Local reports and browser policies can reject ClipboardItem.
        }
    }
    try {
        return copyTableSelection(clipboardTable);
    } catch (error) {
        return false;
    }
}

// LeafyGreen "Copy" icon (mongodb/leafygreen-ui, packages/icon/src/glyphs/Copy.svg)
var COPY_ICON =
    '<svg viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">' +
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M1 5.71428V10.2857C1 11.2325 1.76751 12 2.71429 12H5.75V7.10957C5.75 6.54414 5.97724 6.00244 6.38065 5.60623L8.67403 3.35381C8.77447 3.25516 8.88376 3.16757 9 3.09182V2.71429C9 1.76751 8.23249 1 7.28571 1H5.8V4.42857C5.8 5.13865 5.22437 5.71428 4.51429 5.71428H1ZM9 4.78571L7.25654 6.49804C7.24689 6.50752 7.23749 6.5172 7.22834 6.52708C7.22208 6.53383 7.21594 6.54068 7.20991 6.54762C7.07504 6.70295 7 6.90234 7 7.10957V7.79762H9H10.0095C10.4829 7.79762 10.8667 7.41386 10.8667 6.94047V4H10.1505C9.92587 4 9.7102 4.0882 9.54992 4.24562L9 4.78571ZM4.86667 1H4.15053C3.92587 1 3.7102 1.0882 3.54992 1.24562L1.25654 3.49804C1.09244 3.65921 1 3.87957 1 4.10957V4.79762H4.00952C4.48291 4.79762 4.86667 4.41386 4.86667 3.94047V1ZM7 12V8.71428H9H10.5143C11.2244 8.71428 11.8 8.13865 11.8 7.42857V4H13.2857C14.2325 4 15 4.76751 15 5.71429V13.2857C15 14.2325 14.2325 15 13.2857 15H8.71429C7.76751 15 7 14.2325 7 13.2857V12Z"/>' +
    "</svg>";

// LeafyGreen "Checkmark" icon, shown when the table has been copied.
var CHECKMARK_ICON =
    '<svg viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">' +
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M6.30583 9.05037L11.7611 3.59509C12.1516 3.20457 12.7848 3.20457 13.1753 3.59509L13.8824 4.3022C14.273 4.69273 14.273 5.32589 13.8824 5.71642L6.81525 12.7836C6.38819 13.2106 5.68292 13.1646 5.31505 12.6856L2.26638 8.71605C1.92998 8.27804 2.01235 7.65025 2.45036 7.31385L3.04518 6.85702C3.59269 6.43652 4.37742 6.53949 4.79792 7.087L6.30583 9.05037Z"/>' +
    "</svg>";

/**
 * The button keeps its icon; only the label text changes.
 */
function setTableCopyLabel(button, text, icon) {
    button.innerHTML = (icon || COPY_ICON) + '<span class="table-copy-label"></span>';
    button.querySelector(".table-copy-label").textContent = text;
}

function addTableCopyButtons() {
    document.querySelectorAll("table").forEach(function (table, index) {
        var wrapper = document.createElement("div");
        wrapper.className = "table-copy-wrapper";
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);

        var toolbar = document.createElement("div");
        toolbar.className = "table-copy-toolbar";
        var button = document.createElement("button");
        button.type = "button";
        button.className = "table-copy-button";
        setTableCopyLabel(button, "Copy Table");
        button.setAttribute("aria-label", "Copy table " + (index + 1));
        toolbar.appendChild(button);
        wrapper.insertBefore(toolbar, table);

        button.addEventListener("click", async function () {
            var copied = await copyTable(table);
            setTableCopyLabel(button, copied ? "Copied!" : "Copy failed", copied ? CHECKMARK_ICON : COPY_ICON);
            setTimeout(function () { setTableCopyLabel(button, "Copy Table"); }, 2000);
        });
    });
}
