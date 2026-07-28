var charts = [];

if (typeof Chart !== "undefined") {
    if (typeof ChartDataLabels !== "undefined") {
        try { Chart.register(ChartDataLabels); } catch (e) {}
    }
    Chart.defaults.plugins.datalabels = { display: false };

    // Use an offscreen canvas for reliable text measurement during beforeLayout
    var _measureCanvas = document.createElement("canvas");
    var _measureCtx = _measureCanvas.getContext("2d");

    function _measurePieLabels(chart) {
        var threshold = window.PIE_LABEL_THRESHOLD || 0;
        var total = chart.data.datasets[0].data.reduce(function (a, b) { return a + b; }, 0);
        if (total <= 0) return { maxLeft: 0, maxRight: 0 };
        _measureCtx.font = "bold 11px sans-serif";
        var maxLeft = 0, maxRight = 0;
        // Assume roughly half go to each side; measure all and take max for both
        for (var i = 0; i < chart.data.labels.length; i++) {
            var value = chart.data.datasets[0].data[i];
            var pct = (value / total) * 100;
            if (pct < threshold) continue;
            var text = chart.data.labels[i] + "  " + pct.toFixed(1) + "%";
            var w = _measureCtx.measureText(text).width;
            if (w > maxLeft) maxLeft = w;
            if (w > maxRight) maxRight = w;
        }
        return { maxLeft: maxLeft, maxRight: maxRight };
    }

    var PieLabelPlugin = {
        id: "pieLabelPlugin",
        beforeLayout: function (chart) {
            if (chart.config.type !== "pie" && chart.config.type !== "doughnut") return;
            var measured = _measurePieLabels(chart);
            var labelPad = 10; // gap between pie edge and label text
            // Set padding so the pie shrinks to make room for labels
            chart.options.layout = {
                padding: {
                    left: Math.ceil(measured.maxLeft) + labelPad,
                    right: Math.ceil(measured.maxRight) + labelPad,
                    top: 5,
                    bottom: 5,
                }
            };
        },
        afterDraw: function (chart) {
            if (chart.config.type !== "pie" && chart.config.type !== "doughnut") return;
            var meta = chart.getDatasetMeta(0);
            if (!meta || !meta.data.length) return;
            var total = meta.total || 0;
            if (total <= 0) return;
            var threshold = window.PIE_LABEL_THRESHOLD || 0;
            var ctx = chart.ctx;
            var area = chart.chartArea;
            var fontSize = 11;
            var fontStr = "bold " + fontSize + "px sans-serif";

            var leftItems = [];
            var rightItems = [];

            meta.data.forEach(function (arc, i) {
                var value = chart.data.datasets[0].data[i];
                var pct = (value / total) * 100;
                if (pct < threshold) return;
                var angle = (arc.startAngle + arc.endAngle) / 2;
                var label = chart.data.labels[i];
                var text = label + "  " + pct.toFixed(1) + "%";
                var item = { angle: angle, arc: arc, text: text, pct: pct };
                if (Math.cos(angle) >= 0) {
                    rightItems.push(item);
                } else {
                    leftItems.push(item);
                }
            });

            var sortByAngle = function (a, b) { return a.angle - b.angle; };
            leftItems.sort(sortByAngle);
            rightItems.sort(sortByAngle);

            var lineGap = 6;
            var spacing = fontSize + 5;

            ctx.save();
            ctx.font = fontStr;
            ctx.textBaseline = "middle";

            // Right-side labels
            var labelX = area.right + lineGap;
            var y = area.top + spacing;
            ctx.textAlign = "left";
            rightItems.forEach(function (item) {
                ctx.fillStyle = "#333";
                ctx.fillText(item.text, labelX, y);
                var outer = item.arc.outerRadius;
                var sx = item.arc.x + Math.cos(item.angle) * outer;
                var sy = item.arc.y + Math.sin(item.angle) * outer;
                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.lineTo(area.right, sy);
                ctx.lineTo(labelX - 2, y);
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1;
                ctx.stroke();
                y += spacing;
            });

            // Left-side labels
            labelX = area.left - lineGap;
            y = area.top + spacing;
            ctx.textAlign = "right";
            leftItems.forEach(function (item) {
                ctx.fillStyle = "#333";
                ctx.fillText(item.text, labelX, y);
                var outer = item.arc.outerRadius;
                var sx = item.arc.x + Math.cos(item.angle) * outer;
                var sy = item.arc.y + Math.sin(item.angle) * outer;
                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.lineTo(area.left, sy);
                ctx.lineTo(labelX + 2, y);
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1;
                ctx.stroke();
                y += spacing;
            });

            ctx.restore();
        }
    };
    Chart.register(PieLabelPlugin);

    // Hide legend for pie/doughnut — labels rendered by custom plugin
    Chart.overrides.pie.plugins = Chart.overrides.pie.plugins || {};
    Chart.overrides.pie.plugins.legend = { display: false };
    Chart.overrides.doughnut.plugins = Chart.overrides.doughnut.plugins || {};
    Chart.overrides.doughnut.plugins.legend = { display: false };
}
