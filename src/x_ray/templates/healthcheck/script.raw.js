VIEWPORT_WIDTH = 1200;
charts = charts || [];

hljs.addPlugin(new CopyButtonPlugin({
    hook: (_, el) => el.textContent,
    callback: function () { return false; }
}));

hljs.highlightAll();
