/* Shared code copy-to-clipboard feature (issue #334).
 *
 * - Inline code: every backtick-wrapped string (markdown <code>, not inside
 *   <pre>) gets a small copy icon that flows after the text.
 * - Code blocks: the highlightjs-copy button (which renders "Copy" text) is
 *   taken over and restyled to the same icon, top-right of the block.
 * Clicking copies the string and shows a transient ✓ confirmation.
 */

// LeafyGreen "Copy" icon (mongodb/leafygreen-ui, packages/icon/src/glyphs/Copy.svg)
var CODE_COPY_ICON =
    '<svg viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">' +
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M1 5.71428V10.2857C1 11.2325 1.76751 12 2.71429 12H5.75V7.10957C5.75 6.54414 5.97724 6.00244 6.38065 5.60623L8.67403 3.35381C8.77447 3.25516 8.88376 3.16757 9 3.09182V2.71429C9 1.76751 8.23249 1 7.28571 1H5.8V4.42857C5.8 5.13865 5.22437 5.71428 4.51429 5.71428H1ZM9 4.78571L7.25654 6.49804C7.24689 6.50752 7.23749 6.5172 7.22834 6.52708C7.22208 6.53383 7.21594 6.54068 7.20991 6.54762C7.07504 6.70295 7 6.90234 7 7.10957V7.79762H9H10.0095C10.4829 7.79762 10.8667 7.41386 10.8667 6.94047V4H10.1505C9.92587 4 9.7102 4.0882 9.54992 4.24562L9 4.78571ZM4.86667 1H4.15053C3.92587 1 3.7102 1.0882 3.54992 1.24562L1.25654 3.49804C1.09244 3.65921 1 3.87957 1 4.10957V4.79762H4.00952C4.48291 4.79762 4.86667 4.41386 4.86667 3.94047V1ZM7 12V8.71428H9H10.5143C11.2244 8.71428 11.8 8.13865 11.8 7.42857V4H13.2857C14.2325 4 15 4.76751 15 5.71429V13.2857C15 14.2325 14.2325 15 13.2857 15H8.71429C7.76751 15 7 14.2325 7 13.2857V12Z"/>' +
    "</svg>";

function fallbackCopyText(text, onDone) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
        document.execCommand("copy");
        onDone();
    } catch (e) { /* ignore */ }
    document.body.removeChild(ta);
}

function copyCodeText(text, btn) {
    var onDone = function () {
        btn.classList.add("code-copied");
        btn.title = "Copied";
        setTimeout(function () {
            btn.classList.remove("code-copied");
            btn.title = "Copy";
        }, 1500);
    };
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(onDone, function () { fallbackCopyText(text, onDone); });
    } else {
        fallbackCopyText(text, onDone);
    }
}

/* Reconstruct the text of a <pre> block. Report content is often rendered as
 * <br> line breaks and &nbsp; indentation (not literal newlines), so
 * textContent alone would lose the line breaks. */
function preBlockText(pre) {
    var out = "";
    (function walk(node) {
        node.childNodes.forEach(function (c) {
            if (c.nodeType === 3) {
                out += c.nodeValue;
            } else if (c.nodeType === 1) {
                if (c.tagName === "BR") {
                    out += "\n";
                } else {
                    walk(c);
                }
            }
        });
    })(pre);
    return out.replace(/\u00a0/g, " ");
}

/* Inline (backtick) code: add a copy icon inside each <code> element. */
function inlineCodeCopySetup() {
    var codes = document.querySelectorAll("code");
    codes.forEach(function (code) {
        if (code.classList.contains("code-copyable")) return;
        // Skip code blocks (handled below) and our own chrome.
        if (code.closest("pre") || code.closest(".risk-tooltip") || code.closest(".code-copy-btn")) return;
        code.classList.add("code-copyable");

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "code-copy-btn";
        btn.setAttribute("aria-label", "Copy code");
        btn.title = "Copy";
        btn.innerHTML = CODE_COPY_ICON;
        btn.addEventListener("click", function () { copyCodeText(code.textContent || "", btn); });
        code.appendChild(btn);
    });
}

/* Code blocks: take over the highlightjs-copy button and restyle it as the
 * same icon (top-right of the block) with our own copy behavior, so it never
 * conflicts with the "Copy"/"Copied!" text swapping of the hljs plugin.
 * Bare <pre> blocks (e.g. JSON samples inside tables) that hljs does not
 * manage get the same top-right icon too. */
function blockCodeCopySetup() {
    document.querySelectorAll(".hljs-copy-button").forEach(function (btn) {
        if (btn.dataset.codeCopyUnified) return;
        var wrapper = btn.closest(".hljs-copy-wrapper");
        if (!wrapper) return; // only manage buttons that live in an hljs wrapper
        var code = wrapper.querySelector("pre code") || wrapper.querySelector("code");
        if (!code) {
            btn.remove();
            return;
        }
        // Replace the button to drop the hljs plugin's own click handler.
        var fresh = btn.cloneNode(false);
        btn.parentNode.replaceChild(fresh, btn);
        fresh.dataset.codeCopyUnified = "1";
        fresh.setAttribute("aria-label", "Copy code");
        fresh.title = "Copy";
        fresh.innerHTML = CODE_COPY_ICON;
        fresh.addEventListener("click", function () { copyCodeText(preBlockText(code), fresh); });
    });

    document.querySelectorAll("pre").forEach(function (pre) {
        if (pre.classList.contains("hljs-copy-wrapper") || pre.closest(".risk-tooltip")) return;
        if (pre.dataset.codeCopyUnified) return;
        pre.dataset.codeCopyUnified = "1";
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "hljs-copy-button"; // reuse the block-button styles
        btn.dataset.codeCopyUnified = "1";
        btn.setAttribute("aria-label", "Copy code");
        btn.title = "Copy";
        btn.innerHTML = CODE_COPY_ICON;
        btn.addEventListener("click", function () { copyCodeText(preBlockText(pre), btn); });
        pre.appendChild(btn);
    });
}

/* Inline code and code blocks can both be set up once the document model is
 * ready: the module scripts (hljs.highlightAll and the like) run while the
 * page parses, i.e. before DOMContentLoaded, so the buttons they create exist
 * by the time this runs. The takeover only manages buttons inside an hljs
 * wrapper and never removes the bare-<pre> buttons it added itself. */
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
        inlineCodeCopySetup();
        blockCodeCopySetup();
    });
} else {
    inlineCodeCopySetup();
    blockCodeCopySetup();
}
