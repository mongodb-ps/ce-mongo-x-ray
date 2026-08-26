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
        button.textContent = "Copy Table";
        button.setAttribute("aria-label", "Copy table " + (index + 1));
        toolbar.appendChild(button);
        wrapper.insertBefore(toolbar, table);

        button.addEventListener("click", async function () {
            var copied = await copyTable(table);
            button.textContent = copied ? "Copied!" : "Copy failed";
            setTimeout(function () { button.textContent = "Copy Table"; }, 2000);
        });
    });
}
