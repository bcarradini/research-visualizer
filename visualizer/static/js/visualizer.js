
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
            category: null,
            categories: {},
            classification: null,
            classifications: {},
            entry: null,
            entryAbstract: null,
            entries: {},
            errors: [],
            minNodeSize: 16,
            nodeSizeMultiplier: 40,
            query: null,
            results: {},
            search: null,
            searches: null, // begin with null to distinguish from [], which indicates "no old searches"
            searchResults: null,
            searchResultSources: {},
            source: null,
            spokeNodes: [],

            // map external resources to instance data
            isEmpty: _.isEmpty,
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function() {
        this.fetchOldSearchResults()
        this.fetchSubjectAreaClassifications()
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
            return (this.searches == null) || _.isEmpty(this.categories)
        },
        selectingSearch() {
            return this.search == null
        },
        loadingSearchResults() {
            return this.searchResults == null
        },
        classificationEntries() {
            return (this.classification ? this.entries[this.classification] : null) || []
        },
        eventHandlers() {
            // Event handlers for network graph
            // Ref: https://dash14.github.io/v-network-graph/reference.html#eventhandlers
            return {
                // Handle node click events
                'node:click': (event) => {
                    console.log('TEMP: event.node =', event.node)
                    // If node is not the hub node (''), process click event
                    if (event.node != '') {
                        let node = this.spokeNodes.find(n => n.nodeId == event.node)
                        console.log('TEMP: node =', node)
                        if (this.classification) {
                            this.enterSource(node.vizId)
                        } else if (this.category) {
                            this.enterClassification(node.vizId) // vizId will be the classification code
                        } else {
                            this.enterCategory(node.vizId) // node.vizId will be the category abbreviation
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
            if (newSearch) {
                if (newSearch.query != (oldSearch && oldSearch.query) || newSearch.id != (oldSearch && oldSearch.id)) {
                    if (newSearch.id) {
                        this.fetchOldSearchResults(newSearch.id)
                    } else {
                        this.fetchNewSearchResults(newSearch.query) // for now, implicitly search all categories
                    }
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
            this.errors = []
            this.category = null
            this.classification = null
            this.entries = {}
            this.searchResults = null
        },

        // 
        // -- Graph nodes
        // 

        // Setup graph spoke nodes based on search results, which may be first-level results across
        // all categories or second-level results across all classifications within a category
        async setupSpokeNodes(category=null, classification=null) {
            console.log('TEMP: setupSpokeNodes(): category =', category)
            console.log('TEMP: setupSpokeNodes(): classification =', classification)
            // Identify results set
            let results = this.searchResults
            if (category) {
                results = this.searchResults[category]
            } else if (classification) {
                results = this.searchResultSources[classification]
            }
            console.log('TEMP: setupSpokeNodes(): results =', results)
            if (_.isEmpty(results)) return
 
            // Clear out spoke nodes on instance and wait for DOM to update; otherwise, the NetworkGraph child component
            // will be updated instead of being unmounted/mounted, leading to rendering issues. 
            this.spokeNodes = []
            await nextTick()
 
            // Determine which nodes as the largest result count (for scaling node sizes)
            let maxCount = Math.max(...Object.entries(results).map(([key, obj]) => {
                // When viewing results for a specific category, select `count` from each object (i.e. classification);
                // when viewing for all categories, select `total.count` for each object (i.e. category)
                return (category || classification) ? obj.count : obj.total.count
            }))
 
            // Assemble spoke nodes to visually represent search results
            let nodes = []
            for (const [key, obj] of Object.entries(results)) {
                // Identify appropriate results count and nodeId based on whether we're viewing results for a specific
                // classification, a specific category, or for all categories
                if (category && key == 'total') continue
                let count = (category || classification) ? obj.count : obj.total.count
                let label = (category || classification) ? obj.name : this.categories[key].name
                let vizId = classification ? obj.id : key
                // Add node to list
                nodes.push({ 
                    name: `${count}`, // displayed on the graph
                    nodeId: label, // displayed on the graph
                    vizId: vizId, // what we need when processing click events
                    size: this.getNodeSize(count, maxCount),
                    color: this.getNodeColor(label),
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

        // 
        // -- Navigation
        // 

        beforeUnloadWarning(event) {
            event.preventDefault()
            event.returnValue = "Are you sure you want to exit the tool?"
            return event.returnValue
        },

        exitSearch() {
            // Clear category on instance; setup spoke nodes to view inter-category results
            this.search = null
            this.resetSearchResults()
        },

        enterCategory(category) {
            // Set category on instance; setup spoke nodes to view intra-category results
            this.category = category
            this.setupSpokeNodes(category)
        },

        exitCategory() {
            // Clear category on instance; setup spoke nodes to view inter-category results
            this.category = null
            this.classification = null
            this.source = null
            this.entry = null
            this.errors = []
            this.setupSpokeNodes()
        },

        async enterClassification(classification) {
            // Set classification on instance; setup spoke nodes to view intra-classification results
            this.classification = classification
            await this.fetchSearchSources(this.search.id, classification)
            if (this.searchResultSources[classification] !== undefined) {
                this.setupSpokeNodes(null, classification)
            }
        },

        exitClassification() {
            // Clear classification on instance; setup spoke nodes to view inter-classification results
            this.classification = null
            this.source = null
            this.entry = null
            this.errors = []
            this.setupSpokeNodes(this.category)
        },

        enterSource(source) {
            this.source = source
            this.fetchSearchEntries(this.search.id, this.classification, source)
        },

        exitSource(source) {
            this.source = null
            this.entry = null
            this.errors = []
            this.setupSpokeNodes(null, this.classification)
        },

        enterEntry(entry) {
            this.entry = entry
            this.entry.abstract = 'Blah blah blah blah blah'
            // this.fetchAbstract(this.entry.scopus_id)
        },

        exitEntry() {
            this.entry = null
            this.errors = []
            this.setupSpokeNodes(null, this.classification)
        },

        // 
        // -- API fetches
        // 

        async fetchSubjectAreaClassifications() {
            let response = await internalGet('/subject-area-classifications')
            if (response) {
                this.categories = response.categories
                // this.classifications = response.classifications
            }
        },

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
                this.errors.push(`Failed to retrieve existing search results`)
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
                this.errors.push(`Failed to retrieve new search results`)
            }
        },

        async fetchSearchSources(search_id, classification) {
            // Fetch data
            let data = {classification: classification}
            let response = await internalGet(`/search-results/${search_id}/sources?classification=${classification}`)
            if (response) {
                this.searchResultSources = {...this.searchResultSources, [classification]: response.results}
            } else {
                this.errors.push(`Failed to retrieve sources`)
            }
        },

        async fetchSearchEntries(search_id, classification, source) {
            // Fetch data
            let data = {classification: classification}
            // TODO: Handle pagination
            let response = await internalGet(`/search-results/${search_id}/entries?classification=${classification}&source=${source}&limit=100&offset=0`)
            if (response) {
                this.entries = {...this.entries, [classification]: response.results}
            } else {
                this.errors.push(`Failed to retrieve entries`)
            }
        },
    },
})

app.use(VNetworkGraph)
app.mount('#visualizer')
