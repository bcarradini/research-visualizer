
// 3rd party
import { createApp } from 'vue'
import VNetworkGraph from 'v-network-graph'

// Internal
import {internalGet, internalPost} from './api'
import NetworkGraph from './partials/network_graph'

const app = createApp({
    delimiters: ['${', '}'],
    components: {
        'network-graph': NetworkGraph,
    },

    //
    // -- Initial state
    //

    data: function() {
        return {
            categories: [],
            classifications: [],
            errors: [],
            lastSearch: {
                query: null,
            },
            loadingResults: false,
            minNodeSize: 16,
            nodeSizeMultiplier: 32,
            query: null,
            results: {},
            searchCategory: null,
            spokeNodes: [],

            // map external resources to instance data
            isEmpty: _.isEmpty,
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function() {
        this.fetchSubjectAreaClassifications()
    },

    mounted: function() {
        window.addEventListener("beforeunload", this.beforeUnloadWarning)
    },

    destroyed: function() {
        window.removeEventListener("beforeunload", this.beforeUnloadWarning)
    },

    // 
    // -- Computed properties
    // 

    computed: {
        loadingPage() { 
            return this.categories.length == 0
        },
        eventHandlers() {
            // Ref: https://dash14.github.io/v-network-graph/reference.html#eventhandlers
            return {
                'node:click': (event) => {
                    if (event.node != '') { // ignore events for hub node
                        this.searchCategory = event.node
                    }
                },
            }
        },
    },

    //
    // -- Methods
    // 

    methods: {
        initResultsWithCategories(categories=[]) {
            let results = {}
            for (let category of categories) {
                results[category] = {}
            }
            return results
        },

        search() {
            let query = (this.query || '').trim()
            // TODO: put this back eventually
            // if (query && query != this.lastSearch.query) {
                // this.fetchSearchResults(query, this.categories)
            // }
            // TEMP
            this.query = 'social media'
            this.lastSearch.query = 'social media'
            this.spokeNodes = [{"name":"77","nodeId":"AGRI","size":40.64,"color":"#dda01e"},{"name":"90","nodeId":"ARTS","size":44.8,"color":"#70ca1e"},{"name":"35","nodeId":"BIOC","size":27.2,"color":"#5b1c1f"},{"name":"57","nodeId":"BUSI","size":34.239999999999995,"color":"#e9491f"},{"name":"5","nodeId":"CENG","size":17.6,"color":"#9b811f"},{"name":"79","nodeId":"CHEM","size":41.28,"color":"#cd8b1f"},{"name":"96","nodeId":"COMP","size":46.72,"color":"#0fa71f"},{"name":"70","nodeId":"DECI","size":38.4,"color":"#a7f41f"},{"name":"41","nodeId":"DENT","size":29.119999999999997,"color":"#07f61f"},{"name":"33","nodeId":"EART","size":26.560000000000002,"color":"#de5b20"},{"name":"69","nodeId":"ECON","size":38.08,"color":"#fd6220"},{"name":"17","nodeId":"ENER","size":21.44,"color":"#168b20"},{"name":"40","nodeId":"ENGI","size":28.8,"color":"#4b8b20"},{"name":"99","nodeId":"ENVI","size":47.68,"color":"#1c8d20"},{"name":"88","nodeId":"HEAL","size":44.16,"color":"#e8c521"},{"name":"79","nodeId":"IMMU","size":41.28,"color":"#cc5922"},{"name":"63","nodeId":"MATE","size":36.16,"color":"#05ff23"},{"name":"6","nodeId":"MATH","size":17.92,"color":"#08ff23"},{"name":"12","nodeId":"MEDI","size":19.84,"color":"#1d0c24"},{"name":"12","nodeId":"MULT","size":19.84,"color":"#304924"},{"name":"2","nodeId":"NEUR","size":16.64,"color":"#948224"},{"name":"6","nodeId":"NURS","size":17.92,"color":"#48be24"},{"name":"63","nodeId":"PHAR","size":36.16,"color":"#297425"},{"name":"42","nodeId":"PHYS","size":29.439999999999998,"color":"#127725"},{"name":"98","nodeId":"PSYC","size":47.36,"color":"#4da025"},{"name":"59","nodeId":"SOCI","size":34.879999999999995,"color":"#c2eb26"},{"name":"16","nodeId":"VETE","size":21.12,"color":"#602528"}]
            // TEMP
        },

        setupSpokeNodes() {
            // Clear out spoke nodes on instance
            this.spokeNodes = []
            // TODO: comment
            let nodes = []
            let mostEntries = 100 // TODO: get the real max size
            for (const [category, categoryObj] of Object.entries(this.results)) {
                nodes.push({ 
                    name: `${categoryObj.num_entries}`,
                    nodeId: category,
                    size: this.getNodeSize(categoryObj.num_entries, mostEntries),
                    color: this.getNodeColor(category),
                })
            }
            // Set spoke nodes on instance
            this.spokeNodes = nodes
        },

        getNodeColor(str) {
            // Ref: https://stackoverflow.com/a/16348977/9871562
            var hash = 0;
            for (var i = 0; i < str.length; i++) {
                hash = str.charCodeAt(i) + ((hash << 5) - hash);
            }
            var color = '#';
            for (var i = 0; i < 3; i++) {
                var value = (hash >> (i * 8)) & 0xFF;
                color += ('00' + value.toString(16)).substr(-2);
            }
            return color;
        },

        getNodeSize(entries, mostEntries) {
            return this.minNodeSize + (entries/mostEntries)*this.nodeSizeMultiplier
        },

        beforeUnloadWarning(event) {
            event.preventDefault()
            event.returnValue = "Are you sure you want to exit? Your work will be lost."
            return event.returnValue
        },

        // 
        // -- API fetches
        // 

        async fetchSubjectAreaClassifications() {
            let response = await internalGet('/subject-area-classifications')
            if (response) {
                this.categories = response.categories
                this.classifications = response.classifications
                // this.initResultsWithCategories(this.categories)
            }
        },

        async fetchSearchResults(query, categories=[]) {
            // TODO: comment
            this.errors = []
            this.results = {}
            this.loadingResults = true
            // TODO: comment
            for (let category of categories) {
                console.log('TEMP: fetchSearchResults(): category =', category)
                let data = {query: query, categories: [category]}
                let response = await internalPost('/search', data) // TODO: re-factor: create multiple promises and wait for all to resolve
                if (response) {
                    console.log('TEMP: fetchSearchResults(): response.results =', response.results)
                    this.results = {...this.results, ...response.results}
                    console.log('TEMP: fetchSearchResults(): this.results =', this.results)
                } else {
                    this.errors.push(`Failed to retrieve search results for category ${category}`)
                }
            }
            console.log('TEMP: fetchSearchResults(): done with loop')
            // TODO: comment
            this.lastSearch.query = (this.errors.length == 0) ? query : null
            this.loadingResults = false
            // TODO: Check errors first?
            this.setupSpokeNodes()
        },

        async fetchAbstract(scopusId) {
            console.log('TEMP: fetchAbstract(): scopusId =', scopusId)
            let response = await internalGet(`/abstract/${scopusId}`)
            if (response) {
                console.log(response)
            } else {
                // TODO:
            }
        },
    },
})

app.use(VNetworkGraph)
app.mount('#vue-el-index')
