canvas id=variantChartcanvas
script src=httpscdn.jsdelivr.netnpmchart.jsscript
script
const ctx = document.getElementById('variantChart').getContext('2d');
const data = {
    labels {{ results  map(attribute='mutation_desc_aa')  list  safe }},
    datasets [{
        label 'Variants',
        data {{ results  map(attribute='variant_id')  list  safe }},
        backgroundColor 'rgba(54, 162, 235, 0.5)'
    }]
};
const config = {
    type 'bar',
    data data,
    options {}
};
new Chart(ctx, config);
script
