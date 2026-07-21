const FG_COLOR = '#1f2328';
const BG_COLOR = '#ffffff';
Chart.defaults.color = FG_COLOR;

MAX_DATA_POINTS = 1024;
VIEWPORT_WIDTH = 1200;
MAX_LEGENDS = 15;
ANIMATION_DURATION = 100;
ZOOM_OPTIONS = {
    zoom: {
        wheel: { enabled: true, modifierKey: 'ctrl' },
        pinch: { enabled: true },
        drag: { enabled: true },
        mode: 'x'
    },
    pan: { enabled: true, mode: 'x', modifierKey: 'shift' },
    limits: { x: { min: "original", max: "original" } }
};
data = {};
charts = charts || [];

Chart.register(ChartZoom);

hljs.addPlugin(new CopyButtonPlugin({
    hook: (_, el) => el.textContent,
    callback: function () { return false; }
}));

hljs.highlightAll();

function generateRandomColor(alpha = 0.8) {
    const hue = Math.floor(Math.random() * 360);
    const saturation = Math.floor(Math.random() * 30) + 70;
    const lightness = Math.floor(Math.random() * 20) + 50;
    return `hsla(${hue}, ${saturation}%, ${lightness}%, ${alpha})`;
}

function genDefaultLegendLabels(chart) {
    const original = Chart.defaults.plugins.legend.labels.generateLabels(chart);
    return original.map((label, index) => {
        const dataset = chart.data.datasets[index];
        const type = dataset.type;
        if (type === 'line') {
            label.pointStyle = "line";
            label.lineWidth = 4;
        } else if (type === 'bar' || type === "pie") {
            label.pointStyle = "rect";
        } else {
            label.pointStyle = "circle";
        }
        return label;
    });
}

addTableCopyButtons();
