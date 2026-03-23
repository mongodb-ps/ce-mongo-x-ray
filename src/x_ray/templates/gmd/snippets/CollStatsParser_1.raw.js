const labels = Object.keys(data);
const sizes = labels.map((key) => data[key]?.size || 0);
const indexSizes = labels.map((key) => data[key]?.index_size || 0);
const colors = labels.map((_, index) => `hsl(${(index * 360) / Math.max(labels.length, 1)}, 70%, 60%)`);

let wrapper = document.createElement("div");
let canvas = document.createElement("canvas");
wrapper.className = "pie50";
canvas.className = "pie50";
container.appendChild(wrapper);
wrapper.appendChild(canvas);

const sizeCtx = canvas.getContext("2d");
const sizeChart = new Chart(sizeCtx, {
    type: "pie",
    data: {
        labels: labels,
        datasets: [
            {
                data: sizes,
                backgroundColor: colors,
                borderWidth: 1,
            },
        ],
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: "Collection Size Distribution",
            },
            legend: {
                position: "top",
                labels: {
                    usePointStyle: true,
                    pointStyle: "rect",
                },
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

wrapper = document.createElement("div");
canvas = document.createElement("canvas");
wrapper.className = "pie50";
canvas.className = "pie50";
container.appendChild(wrapper);
wrapper.appendChild(canvas);

const indexCtx = canvas.getContext("2d");
const indexChart = new Chart(indexCtx, {
    type: "pie",
    data: {
        labels: labels,
        datasets: [
            {
                data: indexSizes,
                backgroundColor: colors,
                borderWidth: 1,
            },
        ],
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: "Collection Index Size Distribution",
            },
            legend: {
                position: "top",
                labels: {
                    usePointStyle: true,
                    pointStyle: "rect",
                },
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

charts.push(sizeChart);
charts.push(indexChart);
