
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
                },
                node: {
                    draggable: false,
                    normal: {
                        radius: node => node.size,
                        color: node => node.color,
                    },
                    label: {
                        fontSize: 16,
                        text: 'name'
                    },
                },
            },
            hubNode: {
                name: 'query',
                size: 24,
                color: 'black',
                nodeId: '',
            },
            radius: 400,
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function() {
        console.log('TEMP: NetworkGraph.created(): ')
    },

    mounted: function() {
        console.log('TEMP: NetworkGraph.mounted(): ')
    },

    beforeUpdate: function() {
        console.log('TEMP: NetworkGraph.beforeUpdate(): ')
    },

    updated: function() {
        console.log('TEMP: NetworkGraph.updated(): ')
    },

    beforeUnmount: function() {
        console.log('TEMP: NetworkGraph.beforeUnmount(): ')
    },

    unmounted: function() {
        console.log('TEMP: NetworkGraph.unmounted(): ')
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
        nodes() {
            // Initialize nodes object with hub node
            let nodes = {
                [`${this.hubNodeId}`]: this.hubNode
            }
            // Add spoke notes
            for (let i = 0; i < this.spokeNodesCnt; i++) {
                let nodeId = this.spokeNodes[i].nodeId
                nodes[nodeId] = this.spokeNodes[i]
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
            // Define a variation scale from 1 to 3 based on the number of spoke nodes
            let scale = Math.max(1, Math.min(4, Math.floor(this.spokeNodesCnt/15)))
            for (let i = 0; i < this.spokeNodesCnt; i++) {
                let nodeId = this.spokeNodes[i].nodeId
                let mult = 1 + ((i % scale) * 0.2) // scale radians cyclically to spread nodes out for easier reading
                layout['nodes'][nodeId] = {
                    x: (this.radius * mult) * Math.cos(radians),
                    y: (this.radius * mult) * Math.sin(radians),
                }
                radians += this.spokeRadians
            }
            return layout
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
        getTextAnchor(nodeId) {
            console.log('nodeId =', nodeId)
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
