// Print engines do not agree on how they treat `position: fixed` elements
// (Safari keeps painting them, others drop them after the first page), so take
// the report outline out of the layout while printing and put it back
// afterwards. The print stylesheet hides it as well.
(function () {
    var hidden = [];
    var OUTLINE_IDS = ["outline", "expand-outline", "collapse-outline"];

    function hideOutlineForPrint() {
        OUTLINE_IDS.forEach(function (id) {
            var el = document.getElementById(id);
            if (!el || el.style.display === "none") return;
            hidden.push([el, el.getAttribute("style")]);
            el.style.display = "none";
        });
    }

    function restoreOutlineAfterPrint() {
        hidden.forEach(function (entry) {
            var el = entry[0];
            if (entry[1] === null) {
                el.removeAttribute("style");
            } else {
                el.setAttribute("style", entry[1]);
            }
        });
        hidden = [];
    }

    window.addEventListener("beforeprint", hideOutlineForPrint);
    window.addEventListener("afterprint", restoreOutlineAfterPrint);
})();

function formatSize(sizeBytes, decimal = 2) {
    const units = ["B", "KB", "MB", "GB", "TB"];
    for (let unit of units) {
        if (sizeBytes < 1024) {
            return sizeBytes.toFixed(decimal) + " " + unit;
        }
        sizeBytes /= 1024;
    }
    return sizeBytes.toFixed(decimal) + " PB";
}

if (!navigator.clipboard) {
    window.addEventListener("load", function () {
        document.querySelectorAll(".hljs-copy-button").forEach(function (btn) {
            btn.onclick = function () {
                var code = this.closest(".hljs-copy-wrapper").querySelector("code");
                if (!code) return;
                var text = code.textContent || "";
                var ta = document.createElement("textarea");
                ta.value = text;
                ta.style.position = "fixed";
                ta.style.opacity = "0";
                document.body.appendChild(ta);
                ta.select();
                try {
                    document.execCommand("copy");
                    this.innerHTML = "Copied!";
                    var self = this;
                    setTimeout(function () { self.innerHTML = "Copy"; }, 2000);
                } catch (e) { /* ignore */ }
                document.body.removeChild(ta);
            };
        });
    });
}
