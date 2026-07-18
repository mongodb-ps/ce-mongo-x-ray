VIEWPORT_WIDTH = 1200;
charts = [];

hljs.addPlugin(new CopyButtonPlugin({
    hook: (_, el) => el.textContent
}));

hljs.highlightAll();
