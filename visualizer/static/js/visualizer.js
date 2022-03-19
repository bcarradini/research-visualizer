
// 3rd party
import { createApp, nextTick } from 'vue'
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
            errors: [],
            minNodeSize: 16,
            nodeSizeMultiplier: 40,
            query: null,
            results: {},
            category: null,
            classification: null,
            search: null,
            searches: null, // begin with null to distinguish from [], which indicates "no old searches"
            searchResults: null,
            spokeNodes: [],
            previousSpokeNodes: [],

            // map external resources to instance data
            isEmpty: _.isEmpty,
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function() {
        this.fetchOldSearchResults()
        // // TEMP
        // this.search = {
        //     id: 43,
        //     query: 'social media',
        //     categories: ['SOCI', 'AGRI', 'ARTS', 'BIOC', 'BUSI', 'CENG', 'CHEM', 'COMP', 'DECI', 'DENT', 'EART', 'ECON', 'ENER', 'ENGI', 'ENVI', 'HEAL', 'IMMU', 'MATE', 'MATH', 'MEDI', 'MULT', 'NEUR', 'NURS', 'PHAR', 'PHYS', 'PSYC', 'VETE'],
        //     finished: true,
        //     finished_at: '2022-02-26T04:32:04.909Z',
        //     finished_categories: ['SOCI', 'AGRI', 'ARTS', 'BIOC', 'BUSI', 'CENG', 'CHEM', 'COMP', 'DECI', 'DENT', 'EART', 'ECON', 'ENER', 'ENGI', 'ENVI', 'HEAL', 'IMMU', 'MATE', 'MATH', 'MEDI', 'MULT', 'NEUR', 'NURS', 'PHAR', 'PHYS', 'PSYC', 'VETE'],
        // }
        // // TEMP
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
            return this.searches == null
        },
        selectingSearch() {
            return this.search == null
        },
        loadingSearchResults() {
            return this.searchResults == null
        },
        searchResultsHighLevel() {

        },
        eventHandlers() {
            // Event handlers for network graph
            // Ref: https://dash14.github.io/v-network-graph/reference.html#eventhandlers
            return {
                // Handle node click events
                'node:click': (event) => {
                    console.log('TEMP: node:click(): event =', event)
                    if (event.node != '') { // ignore events for hub node
                        if (this.category) {
                            this.enterClassification(event.node)
                        } else {
                            this.enterCategory(event.node)                            
                        }
                    }
                },
            }
        },
    },

    //
    // -- Watchers
    //

    watch: {
        search(newSearch, oldSearch) {
            console.log('TEMP: watch.search(): oldSearch =', oldSearch)
            console.log('TEMP: watch.search(): newSearch =', newSearch)
            if (newSearch.query != (oldSearch && oldSearch.query) || newSearch.id != (oldSearch && oldSearch.id)) {
                if (newSearch.id) {
                    this.fetchOldSearchResults(newSearch.id)
                } else {
                    this.fetchNewSearchResults(newSearch.query) // for now, implicitly search all categories
                }
            }
        }
    },

    //
    // -- Methods
    // 

    methods: {
        // Select existing search results to visualize
        selectSearch(search) {
            this.search = search
        },

        // Generate new search results to visualize
        initiateSearch() {
            this.search = {
                'query': (this.query || '').trim()
            }
        },

        resetSearchResults() {
            // TODO: comment
            this.errors = []
            this.searchResults = null
        },

        // Setup graph spoke nodes based on search results, which may be first-level results across
        // all categories or second-level results across all classifications within a category
        async setupSpokeNodes(category=null) {
            // Identify results set
            let results = category ? this.searchResults[category] : this.searchResults
            if (_.isEmpty(results)) return
 
            // Clear out spoke nodes on instance and wait for DOM to update; otherwise, the NetworkGraph child component
            // will be updated instead of being unmounted/mounted, leading to rendering issues. 
            this.spokeNodes = []
            await nextTick()
 
            // Determine which nodes as the largest result count (for scaling node sizes)
            let maxCount = Math.max(...Object.entries(results).map(([key, obj]) => {
                // When viewing results for a specific category, select `count` from each object (i.e. classification);
                // when viewing for all categories, select `total.count` for each object (i.e. category)
                return category ? obj.count : obj.total.count
            }))
 
            // Assemble spoke nodes to visually represent search results
            let nodes = []
            for (const [key, obj] of Object.entries(results)) {
                // Identify appropriate results count and nodeId based on whether we're viewing results for a specific
                // category or for all categories
                if (category && key == 'total') continue
                let count = category ? obj.count : obj.total.count
                let nodeId = category ? `${key}: ${obj.name}` : key
                // Add node to list
                nodes.push({ 
                    name: `${count}`,
                    nodeId: nodeId,
                    size: this.getNodeSize(count, maxCount),
                    color: this.getNodeColor(nodeId),
                })
            }
 
            // Set spoke nodes on instance
            this.spokeNodes = nodes
        },

        getNodeColor(str) {
            // Ref: https://stackoverflow.com/a/16348977/9871562
            var hash = 0
            for (var i = 0; i < str.length; i++) {
                hash = str.charCodeAt(i) + ((hash << 5) - hash)
            }
            var color = '#'
            for (var i = 0; i < 3; i++) {
                var value = (hash >> (i * 8)) & 0xFF
                color += ('00' + value.toString(16)).substr(-2)
            }
            return color
        },

        getNodeSize(count, maxCount) {
            return this.minNodeSize + (count/maxCount)*this.nodeSizeMultiplier
        },

        beforeUnloadWarning(event) {
            event.preventDefault()
            event.returnValue = "Are you sure you want to exit the tool?"
            return event.returnValue
        },

        enterCategory(category) {
            // Set category on instance; setup spoke nodes to view intra-category results
            this.category = category
            this.setupSpokeNodes(category)
        },

        exitCategory() {
            // Clear category on instance; setup spoke nodes to view inter-category results
            this.category = null
            this.setupSpokeNodes()
        },

        enterClassification(classification) {
            // Set classification on instance; setup spoke nodes to view intra-classification results
            this.classification = classification
            // this.setupSpokeNodes(classification)
        },

        exitClassification() {
            // Clear classification on instance; setup spoke nodes to view inter-classification results
            this.classification = null
            // this.setupSpokeNodes()
        },

        // 
        // -- API fetches
        // 

        async fetchOldSearchResults(search_id=null) {
            // Reset state of search results (if we're fetching a specific set of search results)
            if (search_id) this.resetSearchResults()
            // Fetch data
            let response = await internalGet('/search-results' + (search_id ? `/${search_id}` : ''))
            if (response) {
                if (search_id) {
                    this.searchResults = response.results
                    this.setupSpokeNodes()
                } else {
                    this.searches = response.results
                }
            } else {
                this.errors.push(`Failed to retrieve search results`)
            }
        },

        async fetchNewSearchResults(query, categories=null) {
            // Reset state of search results
            this.resetSearchResults()
            // Fetch data
            let data = {query: query, categories: categories} // if categories is null, all categories will be searched
            let response = await internalPost('/search', data)
            if (response) {
                this.searchresults = response.results
                this.setupSpokeNodes()
            } else {
                this.errors.push(`Failed to retrieve search results`)
            }
        },

        // async fetchSubjectAreaClassifications() {
        //     let response = await internalGet('/subject-area-classifications')
        //     if (response) {
        //         this.categories = response.categories
        //         this.classifications = response.classifications
        //     }
        // },
    },
})

app.use(VNetworkGraph)
app.mount('#vue-el-visualizer')
