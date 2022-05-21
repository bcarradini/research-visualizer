
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
      barThickness: 20,
      maxLabelChars: 55,
    }
  },

  //
  // -- Lifecycle hooks
  //

  created: function() {
  },

  //
  // -- Computed properties
  //

  computed: {
    chartPadding() {
      // Generate array of label lengths for the 3 left-most labels (labels skew to the left)
      let labelChars = this.chartData.labels.slice(0,3).map(l => l.length)
      // Get the max length of the 3 left-most-labels
      let maxLabelChars = Math.min(this.maxLabelChars, Math.max(...labelChars))
      // Scale left padding based on max label length
      return {
        top: 0,
        left: 150 * Math.max(1, (maxLabelChars / this.maxLabelChars)),
        bottom: 0,
        right: 50,
      }
    },
    chartOptions() {
      let vm = this
      return {
        plugins: {
          legend: {
           display: false,
          },
        },
        responsive: false, // don't resize to display; data will easily become unreadable
        layout: {
          padding: vm.chartPadding,     
        },
        scales: {
          x: {
            type: 'category',
            ticks: {
              autoSkip: false,
              callback(value, index, ticks) {
                let label = (this.getLabelForValue(value) || '')
                // Truncate labels
                if (label.length > vm.maxLabelChars) {
                  label = `${label.slice(0,vm.maxLabelChars)}...`
                }
                return label
              },
            },
          },
        },
        onClick: vm.handleChartClick,
        barThickness: vm.barThickness,
        minBarLength: 4,
      }
    },
    width() {
      let bars = this.chartData.labels.length
      return this.chartPadding.left + this.chartPadding.right + (bars * this.barThickness*1.5)
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
    emitChartClick(vizId) {
         
    },
    handleChartClick(event, activeElements, chart) {
      // If there is an active chart element, use its index to unpack the chart dataset
      if (activeElements[0]) {
        let elemIdx = activeElements[0].index
        let vizId = chart.data.datasets[0].vizIds[elemIdx]
        // Emit signal to parent component
        this.$emit('chart-click', vizId)
      }
    },
  },
}

export default BarChart
