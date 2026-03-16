const namespaces = [...new Set(data.map(item => item.ns))];
const labels = [...new Set(data.map(item => item.label))];

const collFragDatasets = labels.map((label, index) => {
    const collFragData = namespaces.map(ns => {
        const item = data.find(d => d.ns === ns && d.label === label);
        return item ? item.collFrag * 100 : 0;
    });

    return {
        label: label,
        data: collFragData,
        backgroundColor: `rgba(${54 + index * 80}, ${162 + index * 30}, ${235 - index * 50}, 0.8)`
    };
});

const indexFragDatasets = labels.map((label, index) => {
    const indexFragData = namespaces.map(ns => {
        const item = data.find(d => d.ns === ns && d.label === label);
        return item ? item.indexFrag * 100 : 0;
    });

    return {
        label: label,
        data: indexFragData,
        backgroundColor: `rgba(${255 - index * 50}, ${99 + index * 40}, ${132 + index * 30}, 0.8)`
    };
});

const mergedDatasets = [
    ...collFragDatasets.map(dataset => ({
        ...dataset,
        label: `${dataset.label} - Collection`
    })),
    ...indexFragDatasets.map(dataset => ({
        ...dataset,
        label: `${dataset.label} - Index`
    }))
];

// Combined Fragmentation Chart
let wrapper = document.createElement('div');
let canvas = document.createElement('canvas');
wrapper.className = "bar";
canvas.className = 'bar';
container.appendChild(wrapper);
wrapper.appendChild(canvas);
const ctx = canvas.getContext('2d');

const chart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: namespaces,
        datasets: mergedDatasets
    },
    options: {
        indexAxis: 'y',
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Fragmentation (%)'
                },
                max: 100
            },
            y: {
                title: {
                    display: true,
                    text: 'Namespace'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Collection / Index Fragmentation by Namespace'
            },
            legend: {
                display: true,
                position: 'right'
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const label = context.dataset.label || '';
                        const value = (context.parsed.x || 0).toFixed(2);
                        return label + ': ' + value + '%';
                    }
                }
            }
        }
    }
});
charts.push(chart);

