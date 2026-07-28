var charts = [];

if (typeof Chart !== "undefined") {
    if (typeof ChartDataLabels !== "undefined") {
        try { Chart.register(ChartDataLabels); } catch (e) {}
    }
    Chart.defaults.plugins.datalabels = {
        display: function (ctx) {
            if (ctx.chart.config.type !== "pie" && ctx.chart.config.type !== "doughnut") return false;
            var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
            var percentage = total > 0 ? (ctx.dataset.data[ctx.dataIndex] / total * 100) : 0;
            var threshold = window.PIE_LABEL_THRESHOLD || 0;
            return percentage >= threshold ? "auto" : false;
        },
        anchor: "end",
        align: "end",
        offset: 8,
        color: "#333",
        font: { weight: "bold", size: 11 },
        formatter: function (value, ctx) {
            var label = ctx.chart.data.labels[ctx.dataIndex];
            var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
            return label + "\n" + (total > 0 ? (value / total * 100).toFixed(1) : "0.0") + "%";
        }
    };

    // Custom plugin to draw leader lines from pie slices to labels
    var PieLeaderLines = {
        id: "pieLeaderLines",
        afterDraw: function (chart) {
            if (chart.config.type !== "pie" && chart.config.type !== "doughnut") return;
            var ctx = chart.ctx;
            var meta = chart.getDatasetMeta(0);
            if (!meta) return;
            var total = meta.total || 0;
            var threshold = window.PIE_LABEL_THRESHOLD || 0;
            ctx.save();
            meta.data.forEach(function (arc, i) {
                var value = chart.data.datasets[0].data[i];
                var percentage = total > 0 ? (value / total * 100) : 0;
                if (percentage < threshold) return;
                var angle = (arc.startAngle + arc.endAngle) / 2;
                var outer = arc.outerRadius;
                var midX = arc.x + Math.cos(angle) * (outer + 8);
                var midY = arc.y + Math.sin(angle) * (outer + 8);
                var endX = arc.x + Math.cos(angle) * (outer + 18);
                var endY = arc.y + Math.sin(angle) * (outer + 18);
                ctx.beginPath();
                ctx.moveTo(arc.x + Math.cos(angle) * outer, arc.y + Math.sin(angle) * outer);
                ctx.lineTo(midX, midY);
                ctx.lineTo(endX, endY);
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1;
                ctx.stroke();
            });
            ctx.restore();
        }
    };
    Chart.register(PieLeaderLines);

    // Hide legend for pie/doughnut charts — datalabels handle labeling
    Chart.overrides.pie.plugins.legend = { display: false };
    Chart.overrides.doughnut.plugins.legend = { display: false };
}
