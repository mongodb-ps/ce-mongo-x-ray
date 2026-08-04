var charts = [];

if (typeof Chart !== "undefined") {
    if (typeof ChartDataLabels !== "undefined") {
        try { Chart.register(ChartDataLabels); } catch (e) { }
    }
    Chart.defaults.plugins.datalabels = { display: false };

    var PieLabelPlugin = {
        id: "pieLabelPlugin",
        beforeLayout: function (chart) {
            if (chart.config.type !== "pie" && chart.config.type !== "doughnut") return;
            // Pie occupies the center 1/2 of the chart width
            var sidePad = Math.round(chart.width / 4);
            var padding = 20;

            // Estimate left/right item count based on slice angles
            var threshold = window.PIE_LABEL_THRESHOLD || 0;
            var data = chart.data.datasets[0].data;
            var total = data.reduce(function (a, b) { return a + b; }, 0);
            var leftCount = 0, rightCount = 0;
            if (total > 0) {
                var currentAngle = -Math.PI / 2; // start from 12 o'clock
                for (var i = 0; i < data.length; i++) {
                    var value = data[i];
                    var sliceAngle = (value / total) * 2 * Math.PI;
                    var midAngle = currentAngle + sliceAngle / 2;
                    var pct = (value / total) * 100;
                    if (pct >= threshold) {
                        if (Math.cos(midAngle) >= 0) rightCount++; else leftCount++;
                    }
                    currentAngle += sliceAngle;
                }
            }

            var fontSize = 11;
            var spacing = fontSize + 5;
            var maxLabelCount = Math.max(leftCount, rightCount);

            // Height needed for labels (first label has spacing offset, then each adds spacing)
            var labelHeight = (maxLabelCount + 1) * spacing;

            // Height for a circular pie: pie occupies center 1/3 of width, so pie side = chart.width / 3
            var pieWidth = chart.width - sidePad * 2;
            var pieHeight = pieWidth; // circular

            var chartHeight = Math.max(pieHeight, labelHeight);

            chart.options.layout = {
                padding: {
                    left: sidePad,
                    right: sidePad,
                    top: padding,
                    bottom: padding,
                }
            };
            chart.options.aspectRatio = chart.width / (chartHeight + padding * 2);
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
            var sortByAngleDesc = function (a, b) { return b.angle - a.angle; };
            rightItems.sort(sortByAngle);
            leftItems.sort(sortByAngleDesc);

            var lineGap = 6;
            var spacing = fontSize + 5;

            ctx.save();
            ctx.font = fontStr;
            ctx.textBaseline = "middle";

            // Compute max text widths for alignment
            var maxRightW = 0;
            rightItems.forEach(function (item) {
                var w = ctx.measureText(item.text).width;
                if (w > maxRightW) maxRightW = w;
            });
            var maxLeftW = 0;
            leftItems.forEach(function (item) {
                var w = ctx.measureText(item.text).width;
                if (w > maxLeftW) maxLeftW = w;
            });

            // Right-side labels — left edges aligned, to the right
            var labelX = chart.width - lineGap;
            // Vertically center the label block against the pie
            var y = area.top + Math.max(spacing, (area.height - spacing * rightItems.length) / 2);
            ctx.textAlign = "left";
            rightItems.forEach(function (item) {
                ctx.fillStyle = "#333";
                var textW = ctx.measureText(item.text).width;
                var textX = labelX - maxRightW;
                ctx.fillText(item.text, textX, y);
                var outer = item.arc.outerRadius;
                var labelAngle = Math.atan2(y - item.arc.y, textX - item.arc.x);
                var mid = (item.arc.startAngle + item.arc.endAngle) / 2;
                var twoPI = 2 * Math.PI;
                labelAngle += Math.round((mid - labelAngle) / twoPI) * twoPI;
                var clampedAngle = Math.max(item.arc.startAngle, Math.min(item.arc.endAngle, labelAngle));
                var sx = item.arc.x + Math.cos(clampedAngle) * outer;
                var sy = item.arc.y + Math.sin(clampedAngle) * outer;
                var dx = 6;
                var dotR = 2;
                var lineEndX = textX - dx - 2;
                ctx.beginPath();
                ctx.moveTo(sx - dx, sy);
                ctx.lineTo(sx + dx, sy);
                ctx.lineTo(lineEndX, y);
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(sx - dx, sy, dotR, 0, 2 * Math.PI);
                ctx.arc(lineEndX, y, dotR, 0, 2 * Math.PI);
                ctx.fillStyle = "#999";
                ctx.fill();
                y += spacing;
            });

            // Left-side labels — right edges aligned, to the left
            labelX = lineGap + maxLeftW;
            // Vertically center the label block against the pie
            y = area.top + Math.max(spacing, (area.height - spacing * leftItems.length) / 2);
            ctx.textAlign = "right";
            leftItems.forEach(function (item) {
                ctx.fillStyle = "#333";
                ctx.fillText(item.text, labelX, y);
                var outer = item.arc.outerRadius;
                var labelAngle = Math.atan2(y - item.arc.y, labelX - item.arc.x);
                var mid = (item.arc.startAngle + item.arc.endAngle) / 2;
                var twoPI = 2 * Math.PI;
                labelAngle += Math.round((mid - labelAngle) / twoPI) * twoPI;
                var clampedAngle = Math.max(item.arc.startAngle, Math.min(item.arc.endAngle, labelAngle));
                var sx = item.arc.x + Math.cos(clampedAngle) * outer;
                var sy = item.arc.y + Math.sin(clampedAngle) * outer;
                var dx = 6;
                var dotR = 2;
                ctx.beginPath();
                ctx.moveTo(sx + dx, sy);
                ctx.lineTo(sx - dx, sy);
                ctx.lineTo(labelX + dx + 2, y);
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(sx + dx, sy, dotR, 0, 2 * Math.PI);
                ctx.arc(labelX + dx + 2, y, dotR, 0, 2 * Math.PI);
                ctx.fillStyle = "#999";
                ctx.fill();
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
