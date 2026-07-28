var charts = [];

if (typeof Chart !== "undefined" && typeof ChartDataLabels !== "undefined") {
    try { Chart.register(ChartDataLabels); } catch (e) {}
    Chart.defaults.plugins.datalabels = {
        display: function (ctx) {
            if (ctx.chart.config.type !== "pie") return false;
            if (ctx.dataset.data.length > 20) return false;
            var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
            var percentage = total > 0 ? (ctx.dataset.data[ctx.dataIndex] / total * 100) : 0;
            var threshold = window.PIE_LABEL_THRESHOLD || 0;
            return percentage >= threshold ? "auto" : false;
        },
        color: "#333",
        font: { weight: "bold", size: 11 },
        formatter: function (value, ctx) {
            var label = ctx.chart.data.labels[ctx.dataIndex];
            var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
            return label + "\n" + (total > 0 ? (value / total * 100).toFixed(1) : "0.0") + "%";
        }
    };
}
