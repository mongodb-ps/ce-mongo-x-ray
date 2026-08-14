var charts = [];

if (typeof Chart !== "undefined") {
    if (typeof ChartDataLabels !== "undefined") {
        try { Chart.register(ChartDataLabels); } catch (e) { }
    }
    Chart.defaults.plugins.datalabels = { display: false };

    // Pick the point on a slice's outer arc where the connector line anchors.
    // The label direction is expressed as the shortest signed distance from
    // the slice start (modular arithmetic, since Chart.js accumulates angles
    // beyond ±π), then clamped with an inset so the anchor never sits on the
    // border between two slices (which looks like a gap, especially near the
    // horizontal axis).
    var pieAnchorAngle = function (arc, labelAngle) {
        var twoPI = 2 * Math.PI;
        var sweep = arc.endAngle - arc.startAngle;
        var la = labelAngle - arc.startAngle;
        la = ((la % twoPI) + twoPI) % twoPI;
        if (la > Math.PI) la -= twoPI;
        var inset = Math.min(sweep * 0.25, 0.2);
        var t = Math.min(Math.max(la, inset), sweep - inset);
        return arc.startAngle + t;
    };

    // How many labels each side (left/right of the pie) may show at most.
    // Configurable via pie_label_per_side in config.json.
    var MAX_PIE_LABELS_PER_SIDE = window.PIE_LABEL_PER_SIDE || 15;

    // Pick the slices whose labels are drawn: at most MAX_PIE_LABELS_PER_SIDE
    // per side, always the highest-ratio ones. `midAngles[i]` is the mid
    // angle of slice i, which decides its side (cos >= 0 → right).
    var selectPieLabels = function (data, total, midAngles) {
        var items = [];
        data.forEach(function (value, i) {
            items.push({ index: i, pct: (value / total) * 100, mid: midAngles[i] });
        });
        items.sort(function (a, b) { return b.pct - a.pct; });
        var left = [];
        var right = [];
        items.forEach(function (item) {
            if (Math.cos(item.mid) >= 0) {
                if (right.length < MAX_PIE_LABELS_PER_SIDE) right.push(item);
            } else if (left.length < MAX_PIE_LABELS_PER_SIDE) {
                left.push(item);
            }
        });
        return { left: left, right: right };
    };

    // Gradient colors for the pie slices: from a deep blue head to an
    // orange-red tail (deliberately high-contrast endpoints), interpolated
    // through the hue circle so adjacent slices stay visually distinct.
    var PIE_GRADIENT_START = 215;   // deep blue
    var PIE_GRADIENT_END = 20;      // orange-red
    var pieGradientColors = function (count) {
        var colors = [];
        if (count <= 0) return colors;
        if (count === 1) return ["hsl(" + PIE_GRADIENT_START + ", 70%, 55%)"];
        var delta = ((PIE_GRADIENT_END - PIE_GRADIENT_START) % 360 + 360) % 360;
        for (var i = 0; i < count; i++) {
            var hue = (PIE_GRADIENT_START + delta * i / (count - 1)) % 360;
            colors.push("hsl(" + hue.toFixed(1) + ", 70%, 55%)");
        }
        return colors;
    };

    var PieLabelPlugin = {
        id: "pieLabelPlugin",
        // Sort the slices by ratio (descending) before Chart.js builds the
        // chart, so the largest slice sits at the top (12 o'clock) and the
        // rest follow clockwise; then apply the gradient colors.
        beforeInit: function (chart) {
            if (chart.config.type !== "pie" && chart.config.type !== "doughnut") return;
            var dataset = chart.data.datasets[0];
            var data = dataset && dataset.data;
            var labels = chart.data.labels;
            if (!data || !labels || data.length === 0) return;
            if (data.length >= 2) {
                var order = data.map(function (v, i) { return i; })
                    .sort(function (a, b) { return data[b] - data[a]; });
                dataset.data = order.map(function (i) { return data[i]; });
                chart.data.labels = order.map(function (i) { return labels[i]; });
            }
            dataset.backgroundColor = pieGradientColors(dataset.data.length);
        },
        beforeLayout: function (chart) {
            if (chart.config.type !== "pie" && chart.config.type !== "doughnut") return;
            // Pie occupies the center 40% of the chart width
            var sidePad = Math.round(chart.width * 0.3);
            var padding = 20;

            // Estimate left/right item count with the same selection rules as
            // afterDraw: at most MAX_PIE_LABELS_PER_SIDE per side, top ratios.
            var data = chart.data.datasets[0].data;
            var total = data.reduce(function (a, b) { return a + b; }, 0);
            var leftCount = 0, rightCount = 0;
            if (total > 0) {
                var currentAngle = -Math.PI / 2; // start from 12 o'clock
                var midAngles = data.map(function (value) {
                    var sliceAngle = (value / total) * 2 * Math.PI;
                    var mid = currentAngle + sliceAngle / 2;
                    currentAngle += sliceAngle;
                    return mid;
                });
                var selection = selectPieLabels(data, total, midAngles);
                rightCount = selection.right.length;
                leftCount = selection.left.length;
            }

            var fontSize = 11;
            var spacing = fontSize + 5;
            var maxLabelCount = Math.max(leftCount, rightCount);

            // Height needed for labels (first label has spacing offset, then each adds spacing)
            var labelHeight = (maxLabelCount + 1) * spacing;

            // Height for a circular pie: pie occupies center 40% of width
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
            var ctx = chart.ctx;
            var area = chart.chartArea;
            var fontSize = 11;
            var fontStr = "bold " + fontSize + "px sans-serif";

            var leftItems = [];
            var rightItems = [];
            // Hit areas of the drawn labels, used to show the full label in an
            // HTML tooltip on hover (the drawn text is plain canvas, so it is
            // not part of Chart.js's own tooltip interaction).
            chart._pieLabelRects = [];

            // Draw at most MAX_PIE_LABELS_PER_SIDE labels per side, always the
            // highest-ratio slices (replaces the old threshold filter).
            var data = chart.data.datasets[0].data;
            var labels = chart.data.labels;
            var midAngles = meta.data.map(function (arc) { return (arc.startAngle + arc.endAngle) / 2; });
            var selection = selectPieLabels(data, total, midAngles);

            var buildItem = function (sel) {
                var arc = meta.data[sel.index];
                var label = labels[sel.index];
                // Truncate long namespaces so the drawn labels do not overlap
                // the pie; the full label is kept for the hover tooltip.
                var labelLength = window.PIE_LABEL_LENGTH || 0;
                var displayLabel = label;
                if (labelLength > 0 && label.length > labelLength) {
                    displayLabel = label.slice(0, labelLength) + "...";
                }
                var text = displayLabel + "  " + sel.pct.toFixed(1) + "%";
                var fullText = label + "  " + sel.pct.toFixed(1) + "%";
                return { angle: (arc.startAngle + arc.endAngle) / 2, arc: arc, text: text, fullText: fullText, pct: sel.pct };
            };

            selection.right.forEach(function (sel) { rightItems.push(buildItem(sel)); });
            selection.left.forEach(function (sel) { leftItems.push(buildItem(sel)); });

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
                chart._pieLabelRects.push({ text: item.fullText, x: textX, y: y - fontSize / 2, w: textW, h: fontSize });
                var outer = item.arc.outerRadius;
                var labelAngle = Math.atan2(y - item.arc.y, textX - item.arc.x);
                var clampedAngle = pieAnchorAngle(item.arc, labelAngle);
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
                var textW = ctx.measureText(item.text).width;
                ctx.fillText(item.text, labelX, y);
                chart._pieLabelRects.push({ text: item.fullText, x: labelX - textW, y: y - fontSize / 2, w: textW, h: fontSize });
                var outer = item.arc.outerRadius;
                var labelAngle = Math.atan2(y - item.arc.y, labelX - item.arc.x);
                var clampedAngle = pieAnchorAngle(item.arc, labelAngle);
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

            // Hover: the drawn labels are plain canvas text, so they never
            // reach Chart.js's own tooltip. Track the cursor over the label
            // hit areas and show an HTML tooltip with the full label.
            var canvas = chart.canvas;
            if (!canvas._pieHoverAttached) {
                canvas._pieHoverAttached = true;
                canvas.addEventListener("mousemove", function (e) {
                    var canvasRect = canvas.getBoundingClientRect();
                    var x = e.clientX - canvasRect.left;
                    var y = e.clientY - canvasRect.top;
                    var hit = null;
                    (chart._pieLabelRects || []).forEach(function (rect) {
                        if (!hit && x >= rect.x && x <= rect.x + rect.w && y >= rect.y && y <= rect.y + rect.h) {
                            hit = rect;
                        }
                    });
                    var tip = window.__pieLabelTooltip;
                    if (hit) {
                        if (!tip) {
                            tip = document.createElement("div");
                            tip.style.cssText =
                                "position:fixed;display:none;background:rgba(51,51,51,.95);color:#fff;" +
                                "padding:4px 8px;border-radius:4px;font:11px sans-serif;pointer-events:none;" +
                                "z-index:1000;max-width:80vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";
                            document.body.appendChild(tip);
                            window.__pieLabelTooltip = tip;
                        }
                        tip.textContent = hit.text;
                        tip.style.left = (e.clientX + 12) + "px";
                        tip.style.top = (e.clientY + 12) + "px";
                        tip.style.display = "block";
                    } else if (tip) {
                        tip.style.display = "none";
                    }
                });
                canvas.addEventListener("mouseleave", function () {
                    if (window.__pieLabelTooltip) window.__pieLabelTooltip.style.display = "none";
                });
            }
        }
    };
    Chart.register(PieLabelPlugin);

    // Hide legend for pie/doughnut — labels rendered by custom plugin
    Chart.overrides.pie.plugins = Chart.overrides.pie.plugins || {};
    Chart.overrides.pie.plugins.legend = { display: false };
    Chart.overrides.doughnut.plugins = Chart.overrides.doughnut.plugins || {};
    Chart.overrides.doughnut.plugins.legend = { display: false };
}
