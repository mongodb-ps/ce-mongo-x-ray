var charts = [];

if (typeof Chart !== "undefined") {
    if (typeof ChartDataLabels !== "undefined") {
        try { Chart.register(ChartDataLabels); } catch (e) {}
    }
    // Disable built-in datalabels — our custom plugin handles pie labeling
    Chart.defaults.plugins.datalabels = { display: false };

    var PieLabelPlugin = {
        id: "pieLabelPlugin",
        beforeLayout: function (chart) {
            if (chart.config.type !== "pie" && chart.config.type !== "doughnut") return;
            var threshold = window.PIE_LABEL_THRESHOLD || 0;
            var total = chart.data.datasets[0].data.reduce(function (a, b) { return a + b; }, 0);
            if (total <= 0) return;
            var ctx = chart.ctx;
            ctx.font = "bold 11px sans-serif";
            var maxLeft = 0, maxRight = 0;
            for (var i = 0; i < chart.data.labels.length; i++) {
                var value = chart.data.datasets[0].data[i];
                var pct = (value / total) * 100;
                if (pct < threshold) continue;
                var text = chart.data.labels[i] + "  " + pct.toFixed(1) + "%";
                var w = ctx.measureText(text).width;
                // Angles aren't available in beforeLayout; assume roughly half go to each side
                if (i % 2 === 0) {
                    if (w > maxRight) maxRight = w;
                } else {
                    if (w > maxLeft) maxLeft = w;
                }
            }
            // Ensure minimum padding for labels + lines
            var labelPad = Math.max(maxLeft, maxRight, 0) + 30;
            chart.options.layout = chart.options.layout || {};
            chart.options.layout.padding = chart.options.layout.padding || {};
            if (labelPad > (chart.options.layout.padding.left || 0)) {
                chart.options.layout.padding.left = labelPad;
            }
            if (labelPad > (chart.options.layout.padding.right || 0)) {
                chart.options.layout.padding.right = labelPad;
            }
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
            ctx.save();
            ctx.font = "bold 11px sans-serif";
            ctx.textBaseline = "middle";

            var leftItems = [];
            var rightItems = [];

            meta.data.forEach(function (arc, i) {
                var value = chart.data.datasets[0].data[i];
                var pct = (value / total) * 100;
                if (pct < threshold) return;
                var angle = (arc.startAngle + arc.endAngle) / 2;
                var item = {
                    arc: arc,
                    angle: angle,
                    text: chart.data.labels[i] + "  " + pct.toFixed(1) + "%",
                    value: value,
                    pct: pct,
                };
                if (Math.cos(angle) >= 0) {
                    rightItems.push(item);
                } else {
                    leftItems.push(item);
                }
            });

            // Sort by vertical position (angle from top, clockwise)
            var sortByAngle = function (a, b) { return a.angle - b.angle; };
            leftItems.sort(sortByAngle);
            rightItems.sort(sortByAngle);

            var spacing = 16;
            var lineGap = 6;

            // Right-side labels
            var labelX = area.right + 8;
            var y = area.top + spacing;
            ctx.textAlign = "left";
            rightItems.forEach(function (item) {
                ctx.fillStyle = "#333";
                ctx.fillText(item.text, labelX, y);
                // Leader line: slice edge → right edge of pie → to label
                var outer = item.arc.outerRadius;
                var ex = item.arc.x + Math.cos(item.angle) * outer;
                var ey = item.arc.y + Math.sin(item.angle) * outer;
                ctx.beginPath();
                ctx.moveTo(ex, ey);
                ctx.lineTo(area.right, ey);
                ctx.lineTo(labelX - lineGap, y);
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1;
                ctx.stroke();
                y += spacing;
            });

            // Left-side labels
            labelX = area.left - 8;
            y = area.top + spacing;
            ctx.textAlign = "right";
            leftItems.forEach(function (item) {
                ctx.fillStyle = "#333";
                ctx.fillText(item.text, labelX, y);
                // Leader line: slice edge → left edge of pie → to label
                var outer = item.arc.outerRadius;
                var ex = item.arc.x + Math.cos(item.angle) * outer;
                var ey = item.arc.y + Math.sin(item.angle) * outer;
                ctx.beginPath();
                ctx.moveTo(ex, ey);
                ctx.lineTo(area.left, ey);
                ctx.lineTo(labelX + lineGap, y);
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1;
                ctx.stroke();
                y += spacing;
            });

            ctx.restore();
        }
    };
    Chart.register(PieLabelPlugin);

    // Hide legend for pie/doughnut — labels are now outside with leader lines
    Chart.overrides.pie.plugins.legend = { display: false };
    Chart.overrides.doughnut.plugins.legend = { display: false };
}
