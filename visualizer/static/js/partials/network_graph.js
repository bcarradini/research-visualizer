
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
        'hubNode',
        'spokeNodes',
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
                        radius: 30,
                    },
                    label: {
                        fontSize: 16,
                    },
                },
            }
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
        nodes() {
            let nodes = {}
            console.log('TEMP: NetworkGraph.nodes(): this.hubNode =', this.hubNode)
            console.log('TEMP: NetworkGraph.nodes(): this.spokeNodes =', this.spokeNodes)
            // TODO: comment
            if (this.hubNode) {
                nodes['hub'] = this.hubNode
                if (this.spokeNodes && this.spokeNodes.length) {
                    for (let i = 0; i < this.spokeNodes.length; i++) {
                        let nodeId = this.spokeNodes[i]['nodeId']
                        nodes[nodeId] = this.spokeNodes[i]
                    }
                }
            }
            console.log('TEMP: NetworkGraph.nodes(): nodes =', nodes)
            return nodes
        },
        edges() {
            let edges = {}
            // TODO: comment
            if (this.hubNode && this.spokeNodes && this.spokeNodes.length) {
                for (let i = 0; i < this.spokeNodes.length; i++) {
                    let nodeId = this.spokeNodes[i]['nodeId']
                    edges[`edge${nodeId}`] = {
                        source: 'hub',
                        target: nodeId
                    }
                }
            }
            return edges
        },
        layouts() {
            let layout = {}
            // TODO: comment
            if (this.hubNode && this.spokeNodes && this.spokeNodes.length) {
                layout['nodes'] = {
                    'hub': { x: 0, y: 0 }
                }
                for (let i = 0; i < this.spokeNodes.length; i++) {
                    let nodeId = this.spokeNodes[i]['nodeId']
                    layout['nodes'][nodeId] = { x: 50*i, y: -100 }
                }
            }
            return layout
        },
    },

}

export default NetworkGraph
