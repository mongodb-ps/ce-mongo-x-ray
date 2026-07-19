var charts = [];

if (typeof Chart !== "undefined" && typeof ChartDataLabels !== "undefined") {
    try { Chart.register(ChartDataLabels); } catch (e) {}
    Chart.defaults.plugins.datalabels = {
        display: function (ctx) {
            return ctx.chart.config.type === "pie" && ctx.dataset.data.length <= 20 ? "auto" : false;
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
