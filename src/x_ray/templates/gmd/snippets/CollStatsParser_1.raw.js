const labels = Object.keys(data);
const sizes = labels.map((key) => data[key]?.size || 0);
const indexSizes = labels.map((key) => data[key]?.index_size || 0);

let wrapper = document.createElement("div");
let canvas = document.createElement("canvas");
wrapper.className = "pie100";
canvas.className = "pie100";
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

const smallIndexChart = indexSizes.length <= 10;
wrapper = document.createElement("div");
canvas = document.createElement("canvas");
wrapper.className = "pie100";
canvas.className = "pie100";
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
