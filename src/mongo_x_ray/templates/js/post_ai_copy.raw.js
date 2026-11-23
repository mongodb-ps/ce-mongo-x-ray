/* Copy button for every AI note (issue #378).
 *
 * Notes are blockquotes produced by `mongo_x_ray.shared.ai_note_markdown()`,
 * which stores the model's text in `data-ai-note` on the `.ai-label` element.
 * Copying therefore copies exactly that text - without the "AI Analysis" title
 * and without depending on how the markdown renders the blockquote.
 */
(function () {
    // LeafyGreen "Copy" / "Checkmark" glyphs (mongodb/leafygreen-ui icons)
    var COPY_ICON =
        '<svg viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">' +
        '<path fill-rule="evenodd" clip-rule="evenodd" d="M1 5.71428V10.2857C1 11.2325 1.76751 12 2.71429 12H5.75V7.10957C5.75 6.54414 5.97724 6.00244 6.38065 5.60623L8.67403 3.35381C8.77447 3.25516 8.88376 3.16757 9 3.09182V2.71429C9 1.76751 8.23249 1 7.28571 1H5.8V4.42857C5.8 5.13865 5.22437 5.71428 4.51429 5.71428H1ZM9 4.78571L7.25654 6.49804C7.24689 6.50752 7.23749 6.5172 7.22834 6.52708C7.22208 6.53383 7.21594 6.54068 7.20991 6.54762C7.07504 6.70295 7 6.90234 7 7.10957V7.79762H9H10.0095C10.4829 7.79762 10.8667 7.41386 10.8667 6.94047V4H10.1505C9.92587 4 9.7102 4.0882 9.54992 4.24562L9 4.78571ZM4.86667 1H4.15053C3.92587 1 3.7102 1.0882 3.54992 1.24562L1.25654 3.49804C1.09244 3.65921 1 3.87957 1 4.10957V4.79762H4.00952C4.48291 4.79762 4.86667 4.41386 4.86667 3.94047V1ZM7 12V8.71428H9H10.5143C11.2244 8.71428 11.8 8.13865 11.8 7.42857V4H13.2857C14.2325 4 15 4.76751 15 5.71429V13.2857C15 14.2325 14.2325 15 13.2857 15H8.71429C7.76751 15 7 14.2325 7 13.2857V12Z"/>' +
        "</svg>";
    var CHECK_ICON =
        '<svg viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">' +
        '<path fill-rule="evenodd" clip-rule="evenodd" d="M6.30583 9.05037L11.7611 3.59509C12.1516 3.20457 12.7848 3.20457 13.1753 3.59509L13.8824 4.3022C14.273 4.69273 14.273 5.32589 13.8824 5.71642L6.81525 12.7836C6.38819 13.2106 5.68292 13.1646 5.31505 12.6856L2.26638 8.71605C1.92998 8.27804 2.01235 7.65025 2.45036 7.31385L3.04518 6.85702C3.59269 6.43652 4.37742 6.53949 4.79792 7.087L6.30583 9.05037Z"/>' +
        "</svg>";

    function showCopied(button) {
        button.innerHTML = CHECK_ICON;
        button.classList.add("ai-copied");
        button.setAttribute("title", "Copied");
        setTimeout(function () {
            button.innerHTML = COPY_ICON;
            button.classList.remove("ai-copied");
            button.setAttribute("title", "Copy");
        }, 1500);
    }

    function fallbackCopy(text, button) {
        var area = document.createElement("textarea");
        area.value = text;
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        try {
            document.execCommand("copy");
            showCopied(button);
        } catch (error) {
            /* ignore: the browser refused the copy */
        }
        document.body.removeChild(area);
    }

    function copyNote(text, button) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(
                function () {
                    showCopied(button);
                },
                function () {
                    fallbackCopy(text, button);
                }
            );
        } else {
            fallbackCopy(text, button);
        }
    }

    function setup() {
        var buttons = document.querySelectorAll(".ai-copy-btn");
        for (var i = 0; i < buttons.length; i++) {
            var button = buttons[i];
            if (button.dataset.aiCopyReady) {
                continue;
            }
            button.dataset.aiCopyReady = "1";
            button.innerHTML = COPY_ICON;
            button.addEventListener("click", function (event) {
                event.preventDefault();
                var label = this.closest(".ai-label");
                var note = (label && label.getAttribute("data-ai-note")) || "";
                if (!note) {
                    return;
                }
                copyNote(note, this);
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setup);
    } else {
        setup();
    }
})();
