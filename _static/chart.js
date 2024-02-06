let marketTime = js_vars.marketTime

function redrawChart(series) {
        Highcharts.chart('highchart', {

            title: {
                text: 'Trade history'
            },
            yAxis: {
                title: {
                    text: 'Price'
                }
            },
            xAxis: {
                title: {
                    text: 'Time (seconds)'
                },
                min: 0,
                max: marketTime ,
            },
            legend: {
                enabled: true
            },

            plotOptions: {
                series: {
                    label: {
                        enabled: true
                    },
                }
            },

            series: series,

            credits: {
                enabled: false
            }
        });
    }