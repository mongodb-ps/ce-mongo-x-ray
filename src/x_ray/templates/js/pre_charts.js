var charts = [];

if (typeof Chart !== "undefined") {
    if (typeof ChartDataLabels !== "undefined") {
        try { Chart.register(ChartDataLabels); } catch (e) {}
    }
    Chart.defaults.plugins.datalabels = {
        display: false,
    };
    Chart.defaults.plugins.labels = {
        render: function (args) {
            var percentage = args.percentage;
            var threshold = window.PIE_LABEL_THRESHOLD || 0;
            if (percentage < threshold) return "";
            return args.label + "\n" + percentage.toFixed(1) + "%";
        },
        fontColor: "#333",
        fontSize: 11,
        fontStyle: "bold",
        position: "outside",
        arc: true,
    };
}
