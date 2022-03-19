
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
            for (let i = 0; i < this.spokeNodesCnt; i++) {
                let nodeId = this.spokeNodes[i].nodeId
                let altRadius = this.radius
                if (i % 2 == 0) {
                    altRadius = altRadius * 1.1 // TODO: adjust scale based on number of nodes
                }
                layout['nodes'][nodeId] = {
                    x: altRadius * Math.cos(radians),
                    y: altRadius * Math.sin(radians),
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
    },
}

export default NetworkGraph
