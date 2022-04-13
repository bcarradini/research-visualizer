
// 3rd party
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Tooltip, BarElement, CategoryScale } from 'chart.js'

// Internal
import htmlTemplate from "~/visualizer/templates/partials/bar_chart.html"

// TODO: comment
ChartJS.register(Tooltip, BarElement, CategoryScale)

// TODO: Rename to HubSpokeGraph?
const BarChart = {
    delimiters: ['${', '}'],
    template: htmlTemplate,
    components: {
        Bar,
    },
    props: [
        'chartData',
    ],

    //
    // -- Initial state
    //

    data() {
        return {
            // chartData: {
            //     labels: [ 'January', 'February', 'March' ],
            //     datasets: [ { data: [40, 20, 12] } ],
            // },
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function() {
        console.log('TEMP: BarChart.created(): ')
    },

    //
    // -- Computed properties
    //

    computed: {
        chartOptions() {
            return {
                plugins: {
                    legend: {
                      display: false,
                    },
                },
                responsive: false, // don't resize to display; data will easily become unreadable
                scales: {
                    x: {
                        type: 'category',
                        ticks: {
                            autoSkip: false,
                        },
                    },
                },
                onClick: function (e) {
                    console.log('TEMP: e =', e)
                    let chart = e.chart
                    console.log('TEMP: chart =', chart)
                    let elemIdx = e.chart.getActiveElements()[0].index
                    console.log('TEMP: elemIdx =', elemIdx)
                    let elemLabel = chart.data.labels[elemIdx]
                    console.log('TEMP: elemLabel =', elemLabel)
                    let elemId = chart.data.datasets[0].vizIds[elemIdx]
                    console.log('TEMP: elemId =', elemId)
                }
            }
        },
        width() {
            return 100 + (this.chartData.labels.length * 25)
        },
        height() {
            return 800
        },
    },

    // 
    // -- Watchers
    // 

    watch: {
    },

    // 
    // -- Methods
    // 

    methods: {
    },
}

export default BarChart
