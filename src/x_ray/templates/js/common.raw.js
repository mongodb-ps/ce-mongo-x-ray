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
                    this.dataset.copied = "true";
                    var self = this;
                    setTimeout(function () { self.innerHTML = "Copy"; self.dataset.copied = "false"; }, 2000);
                } catch (e) { /* ignore */ }
                document.body.removeChild(ta);
            };
        });
    });
}
