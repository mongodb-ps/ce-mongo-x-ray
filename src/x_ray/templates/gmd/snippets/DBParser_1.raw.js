const labels = data.map((item) => item.name);
const storageSizes = data.map((item) => item.storageSize || 0);
const colors = labels.map((_, index) => `hsl(${(index * 360) / Math.max(labels.length, 1)}, 70%, 60%)`);

const wrapper = document.createElement("div");
const canvas = document.createElement("canvas");

wrapper.className = "pie50";
canvas.className = "pie50";

container.appendChild(wrapper);
wrapper.appendChild(canvas);

const ctx = canvas.getContext("2d");
const chart = new Chart(ctx, {
    type: "pie",
    data: {
        labels: labels,
        datasets: [
            {
                data: storageSizes,
                backgroundColor: colors,
                borderWidth: 1,
            },
        ],
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: "right",
                labels: {
                    usePointStyle: true,
                    pointStyle: "rect",
                },
            },
            title: {
                display: true,
                text: "Database Storage Size Distribution",
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const label = context.label || "";
                        const value = context.parsed || 0;
                        const total = context.dataset.data.reduce((sum, current) => sum + current, 0);
                        const percentage = total === 0 ? 0 : ((value / total) * 100).toFixed(2);
                        return `${label}: ${formatSize(value)} (${percentage}%)`;
                    },
                },
            },
        },
    },
});

charts.push(chart);