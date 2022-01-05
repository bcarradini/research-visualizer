
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
            hubNode: null,
            lastSearch: {
                query: null,
            },
            loadingResults: false,
            query: null,
            results: {},
            // TEMP

            // map external resources to instance data
            isEmpty: _.isEmpty,
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function() {
        this.fetchSubjectAreaClassifications()
        // TEMP
        // this.hubNode = { name: 'query' }
        // this.results = {
        //     AGRI: {num_entries: 10},
        //     ARTS: {num_entries: 20},
        //     BIOC: {num_entries: 30},
        // }
        // TEMP
    },

    // 
    // -- Computed properties
    // 

    computed: {
        loadingPage() { 
            return this.categories.length == 0
        },
        spokeNodes() {
            let nodes = []
            for (const [category, categoryObj] of Object.entries(this.results)) {
                nodes.push({ name: `${categoryObj.num_entries}`, nodeId: category})
            }
            return nodes
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
                this.fetchSearchResults(query, ['AGRI','ARTS','BIOC'])
                // this.fetchSearchResults(query, this.categories)
            // }
        },

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
            this.hubNode = { name: 'query' }
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
