
// 3rd party
import VNetworkGraph from "v-network-graph"
// import "v-network-graph/lib/style.css"
import VNetworkGraph from "../../../node_modules/v-network-graph"
// import "../../../node_modules/v-network-graph/lib/style.css"

// Internal
import {internalGet, internalPost} from './api.js'

const app = new Vue({
    delimiters: ['${', '}'],
    el: '#vue-el-index',

    data: function() {
        return {
            categories: [],
            classifications: [],
            errors: [],
            lastSearch: {
                query: null,
            },
            loadingResults: false,
            query: null,
            results: {},

            // TODO
            tempData: {
                tempNodes: [
                    {"id": "Search Query"},
                    {"id": "AGRI"},
                    {"id": "ARTS"},
                    {"id": "MULT"},
                ],
                tempLinks: [
                    {"source": "Search Query", "target": "AGRI"},
                    {"source": "Search Query", "target": "ARTS"},
                    {"source": "Search Query", "target": "MULT"},
                ],
            },
            // TODO

            // map external resources to instance data
            isEmpty: _.isEmpty,
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function() {
        this.fetchSubjectAreaClassifications()
        // TODO: prototype
        // d3.select("#visualization").style("background-color", "red");
        // d3.selectAll("#visualization .circle")
        //         .style("height", function(d, i) {
        //             console.log('TEMP: i =', i)
        //             return 10*(i+1) + "px"
        //         })
    },

    // 
    // -- Computed properties
    // 

    computed: {
        loadingPage() { 
            return this.categories.length == 0
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
                    this.results = {...this.results, ...response.results}
                } else {
                    this.errors.push(`Failed to retrieve search results for category ${category}`)
                }
            }
            console.log('TEMP: fetchSearchResults(): done with loop')
            // TODO: comment
            this.lastSearch.query = (this.errors.length == 0) ? query : null
            this.loadingResults = false
        },

        search() {
            let query = (this.query || '').trim()
            // TODO: put this back eventually
            // if (query && query != this.lastSearch.query) {
                this.fetchSearchResults(query, ['AGRI','ARTS','BIOC'])
                // this.fetchSearchResults(query, this.categories)
            // }
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
