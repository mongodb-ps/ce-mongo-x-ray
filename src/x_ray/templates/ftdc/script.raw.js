function tableText(table) {
    return Array.from(table.rows).map((row) =>
        Array.from(row.cells).map((cell) =>
            cell.innerText.replace(/\t/g, " ").trim()
        ).join("\t")
    ).join("\n");
}

function tableForClipboard(table) {
    const clone = table.cloneNode(true);
    const landscapeWidth = 864;
    const chartColumnWidth = 55;
    const maxImageWidth = 450;
    clone.setAttribute("width", String(landscapeWidth));
    clone.style.width = "9in";
    clone.style.maxWidth = "9in";
    clone.style.tableLayout = "fixed";
    clone.style.borderCollapse = "collapse";
    clone.querySelectorAll("th, td").forEach((cell) => {
        cell.style.overflowWrap = "anywhere";
        cell.style.verticalAlign = "top";
    });
    if (clone.querySelector("img")) {
        Array.from(clone.rows).forEach((row) => {
            const cells = Array.from(row.cells);
            if (!cells.length) return;
            const otherColumnWidth = (100 - chartColumnWidth) / Math.max(1, cells.length - 1);
            cells.forEach((cell, index) => {
                const width = index === cells.length - 1 ? chartColumnWidth : otherColumnWidth;
                cell.setAttribute("width", `${width}%`);
                cell.style.width = `${width}%`;
            });
        });
    }
    clone.querySelectorAll("img").forEach((image) => {
        const sourceWidth = Number(image.getAttribute("width")) || image.naturalWidth || maxImageWidth;
        const sourceHeight = Number(image.getAttribute("height")) || image.naturalHeight;
        const width = Math.min(sourceWidth, maxImageWidth);
        image.setAttribute("width", String(Math.round(width)));
        if (sourceHeight) {
            image.setAttribute("height", String(Math.round(sourceHeight * width / sourceWidth)));
        } else {
            image.removeAttribute("height");
        }
        image.style.display = "block";
        image.style.width = `${width}px`;
        image.style.maxWidth = "100%";
        image.style.height = "auto";
        image.style.objectFit = "contain";
    });
    return clone;
}

function copyTableSelection(table) {
    const selection = window.getSelection();
    if (!selection) return false;
    const container = document.createElement("div");
    container.style.position = "fixed";
    container.style.left = "-10000px";
    container.style.top = "0";
    container.style.width = "9in";
    container.appendChild(table);
    document.body.appendChild(container);
    const previousRanges = [];
    for (let index = 0; index < selection.rangeCount; index++) {
        previousRanges.push(selection.getRangeAt(index));
    }
    const range = document.createRange();
    range.selectNode(table);
    selection.removeAllRanges();
    selection.addRange(range);
    let copied = false;
    try {
        copied = document.execCommand("copy");
    } finally {
        selection.removeAllRanges();
        container.remove();
        previousRanges.forEach((previousRange) => selection.addRange(previousRange));
    }
    return copied;
}

async function copyTable(table) {
    const clipboardTable = tableForClipboard(table);
    const html = clipboardTable.outerHTML;
    const text = tableText(table);
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

document.querySelectorAll("table").forEach((table, index) => {
    const wrapper = document.createElement("div");
    wrapper.className = "table-copy-wrapper";
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);

    const toolbar = document.createElement("div");
    toolbar.className = "table-copy-toolbar";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "table-copy-button";
    button.textContent = "Copy";
    button.setAttribute("aria-label", `Copy table ${index + 1}`);
    toolbar.appendChild(button);
    wrapper.insertBefore(toolbar, table);

    button.addEventListener("click", async () => {
        const copied = await copyTable(table);
        button.textContent = copied ? "Copied!" : "Copy failed";
        setTimeout(() => { button.textContent = "Copy"; }, 2000);
    });
});

if (window.hljs) {
    if (typeof CopyButtonPlugin !== "undefined") {
        hljs.addPlugin(new CopyButtonPlugin({
            autohide: false,
            hook: (_, element) => element.textContent
        }));
    }
    document.querySelectorAll(".metadata-code").forEach((code) => hljs.highlightElement(code));
    document.querySelectorAll("pre code:not(.metadata-code)")
        .forEach((code) => hljs.highlightElement(code));
}
