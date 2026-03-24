const allTimesSet = new Set();
data.forEach(entry => {
    entry.buckets.forEach(b => allTimesSet.add(b.time));
});
// Collect all unique timestamps (sorted) across all filteredData items
const allTimes = Array.from(allTimesSet).sort();

// Build one dataset per filteredData entry (colors assigned automatically by Chart.js)
const datasets = data.map((entry) => {
    const bucketMap = {};
    entry.buckets.forEach(b => { bucketMap[b.time] = b.count; });
    return {
        label: `[${entry.id}] ${entry.sample.msg}`,
        data: allTimes.map(t => bucketMap[t] || 0),
        fill: false,
        tension: 0.3,
        pointRadius: 2
    };
});

console.log("Datasets for chart:", datasets);
const ctx = document.getElementById('canvas_{name}').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: allTimes,
        datasets: datasets
    },
    options: {
        responsive: true,
        animation: { duration: ANIMATION_DURATION },
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    generateLabels: genDefaultLegendLabels
                }
            },
            zoom: ZOOM_OPTIONS
        },
        scales: {
            x: {
                title: { display: true, text: 'Time' }
            },
            y: {
                beginAtZero: true,
                title: { display: true, text: 'Count' }
            }
        }
    }
});
charts.push(chart);
