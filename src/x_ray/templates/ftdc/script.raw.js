if (window.hljs) {
    if (typeof CopyButtonPlugin !== "undefined") {
        hljs.addPlugin(new CopyButtonPlugin({
            autohide: false,
            hook: (_, element) => element.textContent,
            callback: function () { return false; }
        }));
    }
    document.querySelectorAll(".metadata-code").forEach((code) => hljs.highlightElement(code));
    document.querySelectorAll("pre code:not(.metadata-code)")
        .forEach((code) => hljs.highlightElement(code));
}
addTableCopyButtons();
