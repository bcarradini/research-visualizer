
// Internal
import htmlTemplate from "~/visualizer/templates/partials/network_graph.html"

// TODO: Rename to HubSpokeGraph?
const NetworkGraph = {
  delimiters: ['${', '}'],
  template: htmlTemplate,
  components: {},
  props: [
    'spokeNodes',
    'eventHandlers',
  ],

  // 
  // -- Initial state
  //   

  data() {
    return {
      configs: {
        view: {
          panEnabled: false,
          zoomEnabled: false,
          autoPanAndZoomOnLoad: 'fit-content'
        },
        node: {
          draggable: false,
          normal: {
            radius: node => node.size,
            color: node => node.color,
            strokeWidth: 3,
            strokeColor: node => node.color,
          },
          hover: {
            radius: node => node.size,
            color: node => node.color,
            // same stroke width, different color
            strokeWidth: 3,
            strokeColor: '#ffd700', // $gold
          },
          label: {
            fontSize: 16,
            text: 'name',
          },
          zOrder: {
            enabled: true,
            zIndex: (n) => n.zIndex,
            bringToFrontOnHover: true,
            bringToFrontOnSelected: true,
          },
        },
        edge: {
          selectable: false,
          normal: {
            width: 2,
            color: '#e0e0e0', // $midGray
          },
          hover: {
            // same stroke width, same color (prevent visible change on hover)
            width: 2,
            color: '#e0e0e0', // $midGray
          },
          zOrder: {
            enabled: true,
            zIndex: 0,
            bringToFrontOnHover: false,
            bringToFrontOnSelected: false,
          },
        },
      },
      hubNode: {
        name: 'query',
        size: 24,
        color: 'black',
        nodeId: '',
      },
      minRadius: 350,
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
    hubNodeId() {
      return this.hubNode.nodeId
    },
    spokeNodesCnt() {
      return (this.spokeNodes && this.spokeNodes.length) || 0
    },
    spokeRadians() {
      return (this.spokeNodesCnt && (2*Math.PI/this.spokeNodesCnt)) || 0
    },
    concentricCircles() {
      // Return the number of concetric circles, between 1 and 4 inclusive, to use for laying
      // out the spoke nodes (adjacent nodes will be plotted along different circlular paths)
      return (this.spokeNodesCnt && Math.max(1, Math.min(4, Math.floor(this.spokeNodesCnt/12)))) || 0
    },
    nodes() {
      // Initialize nodes object with hub node
      let nodes = {
        [`${this.hubNodeId}`]: this.hubNode
      }
      // Add spoke notes
      for (let i = 0; i < this.spokeNodesCnt; i++) {
        let nodeId = this.spokeNodes[i].nodeId
        nodes[nodeId] = this.spokeNodes[i]
        nodes[nodeId].zIndex = -(i % this.concentricCircles)
      }
      return nodes
    },
    edges() {
      let edges = {}
      // Add edges beteween hub node and each spoke node
      for (let i = 0; i < this.spokeNodesCnt; i++) {
        let nodeId = this.spokeNodes[i].nodeId
        edges[`edge${nodeId}`] = {
          source: this.hubNodeId,
          target: nodeId
        }
      }
      return edges
    },
    layouts() {
      // Initialize layout object with hub node at center
      let layout = {'nodes': {
        [`${this.hubNodeId}`]: {x: 0, y: 0}
      }}
      // Add spoke nodes
      let radians = 0
      for (let i = 0; i < this.spokeNodesCnt; i++) {
        let nodeId = this.spokeNodes[i].nodeId
        // Scale radians cyclically to spread nodes out across concentric circles for easier reading
        let scale = 1 + ((i % this.concentricCircles) * 0.2)
        layout['nodes'][nodeId] = {
          x: (this.minRadius * scale) * Math.cos(radians),
          y: (this.minRadius * scale) * Math.sin(radians),
        }
        radians += this.spokeRadians
      }
      return layout
    },
    graphStyles() {
      return {
        '--svg-width': this.concentricCircles <= 2 ? '1500px' : '2000px',
        '--svg-height': this.concentricCircles <= 2 ? '1500px' : '2000px',
      }
    }
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
    getTextAnchor(nodeId) {
      let nodeLayout = this.layouts.nodes[nodeId] || {}
      let x = nodeLayout.x || 0
      let y = nodeLayout.y || 0
      if (Math.abs(x) / Math.abs(y) > 0.66) {
        if (x < 0) {
          return 'end'
        } else {
          return 'start'
        }
      }
      return 'middle'
    }
  },
}

export default NetworkGraph
