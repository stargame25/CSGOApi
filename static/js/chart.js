var ctx = document.getElementById('myChart').getContext('2d');
var myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['1', '2', '3', '4', '5', '6'],
        datasets: [{
            label: '# of Votes',
            data: [12, 19, 3, 0, 2, 3],
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 99, 132, 1)',
            ],
            fill: false,
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true
                }
            }]
        },
        responsive : false
    }
});


/*
                'rgba(255, 99, 132, 1)',  - red
                'rgba(54, 162, 235, 1)',  - blue
                'rgba(255, 206, 86, 1)',  - yellow
                'rgba(75, 192, 192, 1)',  - green
                'rgba(153, 102, 255, 1)', - purple
                'rgba(255, 159, 64, 1)'   - orange
*/