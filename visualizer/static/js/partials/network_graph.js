
// 3rd party
import { reactive } from 'vue'

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
            radius: 450,
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function() {
        console.log('TEMP: NetworkGraph.created(): ')
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
            for (let i = 0; i < this.spokeNodesCnt; i++) {
                let nodeId = this.spokeNodes[i].nodeId
                layout['nodes'][nodeId] = {
                    x: this.radius * Math.cos(radians),
                    y: this.radius * Math.sin(radians),
                }
                radians += this.spokeRadians
            }
            return layout
        },
    },

    // 
    // -- Methods
    // 

    methods: {
    },
}

export default NetworkGraph
