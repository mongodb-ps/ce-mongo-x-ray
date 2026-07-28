var charts = [];

if (typeof Chart !== "undefined") {
    if (typeof ChartDataLabels !== "undefined") {
        try { Chart.register(ChartDataLabels); } catch (e) {}
    }
    Chart.defaults.plugins.datalabels = { display: false };

    var PieLabelPlugin = {
        id: "pieLabelPlugin",
        // Use beforeDraw to set up font, afterDraw to render labels + lines
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

            // Collect visible items, split left/right by slice midpoint angle
            var leftItems = [];
            var rightItems = [];

            meta.data.forEach(function (arc, i) {
                var value = chart.data.datasets[0].data[i];
                var pct = (value / total) * 100;
                if (pct < threshold) return;
                var angle = (arc.startAngle + arc.endAngle) / 2;
                var label = chart.data.labels[i];
                var text = label + "  " + pct.toFixed(1) + "%";
                ctx.font = fontStr;
                var textW = ctx.measureText(text).width;
                var item = { angle: angle, arc: arc, text: text, textW: textW, pct: pct };
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

    // For pie/doughnut: reserve space for labels via layout padding, hide legend
    Chart.overrides.pie.plugins = Chart.overrides.pie.plugins || {};
    Chart.overrides.pie.plugins.legend = { display: false };
    Chart.overrides.pie.layout = { padding: { left: 60, right: 60, top: 10, bottom: 10 } };
    Chart.overrides.doughnut.plugins = Chart.overrides.doughnut.plugins || {};
    Chart.overrides.doughnut.plugins.legend = { display: false };
    Chart.overrides.doughnut.layout = { padding: { left: 60, right: 60, top: 10, bottom: 10 } };
}
