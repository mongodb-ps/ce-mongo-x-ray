let wrapper = document.createElement('div');
let canvas = document.createElement('canvas');
wrapper.className = "pie";
canvas.className = 'pie';
container.appendChild(wrapper);
wrapper.appendChild(canvas);
const labels = Object.keys(data);
const sizes = Object.values(data).map(item => item.size);
const indexSizes = Object.values(data).map(item => item.index_size);

const colors = labels.map(() =>
    `hsl(${Math.random() * 360}, 70%, 60%)`
);

const ctx = canvas.getContext('2d');
const chart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: sizes,
            backgroundColor: colors,
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'right',
            },
            title: {
                display: true,
                text: 'Data Size Distribution'
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(2);
                        return `${label}: ${value} bytes (${percentage}%)`;
                    }
                }
            }
        }
    }
});
let wrapper2 = document.createElement('div');
let canvas2 = document.createElement('canvas');
wrapper2.className = "pie";
canvas2.className = 'pie';
container.appendChild(wrapper2);
wrapper2.appendChild(canvas2);
const ctx2 = canvas2.getContext('2d');
const chart2 = new Chart(ctx2, {
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: indexSizes,
            backgroundColor: colors,
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'right',
            },
            title: {
                display: true,
                text: 'Index Size Distribution'
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(2);
                        return `${label}: ${value} bytes (${percentage}%)`;
                    }
                }
            }
        }
    }
});
charts.push(chart);
charts.push(chart2);