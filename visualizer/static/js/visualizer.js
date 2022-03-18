
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
            errors: [],
            minNodeSize: 16,
            nodeSizeMultiplier: 40,
            query: null,
            results: {},
            category: null,
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
    },

    // mounted: function() {
    //     window.addEventListener("beforeunload", this.beforeUnloadWarning)
    // },

    // destroyed: function() {
    //     window.removeEventListener("beforeunload", this.beforeUnloadWarning)
    // },

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
                    if (event.node != '') { // ignore events for hub node
                        this.enterCategory(event.node)
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

        setupSpokeNodes() {
            if (this.loadingSearchResults) return
            // Clear out spoke nodes on instance
            this.spokeNodes = []
            // TODO: comment
            let nodes = []
            console.log('TEMP: setupSpokeNodes(): this.searchResults =', this.searchResults)
            let maxCount = Math.max(...Object.entries(this.searchResults).map(([cat, catObj]) => catObj.total.count))
            console.log('TEMP: setupSpokeNodes(): maxCount =', maxCount)
            for (const [category, categoryObj] of Object.entries(this.searchResults)) {
                nodes.push({ 
                    name: `${categoryObj.total.count}`,
                    nodeId: category,
                    size: this.getNodeSize(categoryObj.total.count, maxCount),
                    color: this.getNodeColor(category),
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

        // beforeUnloadWarning(event) {
        //     event.preventDefault()
        //     event.returnValue = "Are you sure you want to exit? Your work will be lost."
        //     return event.returnValue
        // },

        // enterCategory(category) {
        //     // Set category on instance
        //     this.category = category
        //     // Count results for category by classification
        //     let classifications = {}
        //     for (const e of this.searchResults[category].entries) {
        //         for (const c of e.classifications) {
        //             if (c.code in classifications) {
        //                 classifications[c.code]['num_entries'] += 1
        //             } else {
        //                 classifications[c.code] = {
        //                     name: c.name,
        //                     num_entries: 1,
        //                 }
        //             }
        //         }
        //     }
        //     // Clear out spoke nodes on instance
        //     this.spokeNodes = []
        //     // Setup new nodes representing category breakdown
        //     let nodes = []
        //     let maxCount = 100 // TODO: get the real max size
        //     for (const [classCode, classObj] of Object.entries(classifications)) {
        //         console.log('TEMP: enterCategory(): classCode =', classCode)
        //         console.log('TEMP: enterCategory(): classObj =', classObj)
        //         nodes.push({ 
        //             name: `${classObj.num_entries}`,
        //             nodeId: classObj.code,
        //             size: this.getNodeSize(classObj.num_entries, maxCount),
        //             color: this.getNodeColor(classObj.name),
        //         })
        //     }
        //     // Set spoke nodes on instance
        //     this.spokeNodes = nodes
        // },

        // exitCategory() {
        //     // Clear category on instance
        //     this.category = null
        //     // Reset spoke nodes for first-level search
        //     this.spokeNodes = this.previousSpokeNodes
        //     this.previousSpokeNodes = []
        // },

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
