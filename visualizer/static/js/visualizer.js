
// 3rd party
import { createApp, nextTick } from 'vue'
import VNetworkGraph from 'v-network-graph'

// Internal
import {internalDelete, internalGet, internalPost} from './api'
import NetworkGraph from './partials/network_graph'
import BarChart from './partials/bar_chart'

// Constants
const LIMIT = 100

const app = createApp({
  delimiters: ['${', '}'],
  components: {
    'network-graph': NetworkGraph,
    'bar-chart': BarChart,
  },

  //
  // -- Initial state
  //

  data: function() {
    return {
      category: null,
      categories: {},
      chartData: {},
      classification: null,
      entry: null,
      entries: {},
      entriesOffset: 0,
      errors: [],
      minNodeSize: 18,
      nodeSizeMultiplier: 40,
      query: null,
      results: {},
      search: null,
      searchesCompleted: null, // begin with null to distinguish from [], which indicates "no old searches"
      searchesPending: [],
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
    this.fetchSearchResults()
    this.fetchSearchResults({pending: true})
    this.fetchSubjectAreaClassifications()
    // TEMP
    // this.search = {
    //   id: 43,
    //   query: 'social media',
    // }
    // TEMP
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
      return (this.searchesCompleted == null) || _.isEmpty(this.categories)
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
    moreEntries() {
      return this.entries[this.classification] ? this.entriesCount > this.entries[this.classification].length : false
    },
    networkGraphEventHandlers() {
      // Event handlers for network graph
      // Ref: https://dash14.github.io/v-network-graph/reference.html#eventhandlers
      return {
        // Handle node click events
        'node:click': (event) => {
          // If node is not the hub node (''), process click event
          if (event.node != '') {
            let node = this.spokeNodes.find(n => n.nodeId == event.node)
            if (node.name != '0') { // block clicks for 0-count nodes
              if (this.category) {
                this.enterClassification(node.vizId) // vizId will be the classification code
              } else if (this.search) {
                this.enterCategory(node.vizId) // node.vizId will be the category abbreviation
              }              
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
        if (newSearch.id) {
          console.log('search(): fetch old search results', newSearch.id)
          this.fetchSearchResults({searchId: newSearch.id})
        } else if (newSearch.query) {
          console.log('search(): fetch new search results', newSearch.query)
          this.startSearch(newSearch.query) // for now, implicitly search all categories
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

    async deleteSearch(searchId) {
      // Reset state of search results (if we're fetching a specific set of search results)
      if (searchId == null) return
      // Delete search
      let response = await internalDelete(`/search-results/${searchId}`)
      if (response && response.deleted) {
        this.searchesPending = this.searchesPending.filter(s => s.id != searchId)
        this.searchesCompleted = this.searchesCompleted.filter(s => s.id != searchId)
      } else {
        this.errors.push(`Failed to delete search`)
      }
    },

    resetSearchResults() {
      this.searchResults = null
      this.category = null
      this.classification = null
      this.source = null
      this.entries = {}
      this.entry = null
      this.errors = []
    },

    getLabelColor(str) {
      // Ref: https://stackoverflow.com/a/16348977/9871562
      str = str || ''
      let hash = 0
      for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash)
      }
      let color = '#'
      for (let i = 0; i < 3; i++) {
        let value = (hash >> (i * 8)) & 0xFF
        color += ('00' + value.toString(16)).substr(-2)
      }
      return color
    },

    getCategoriesDisplay(search) {
      let categories = search.categories
      // If search was for "all categories," say as much; otherwise, list categories
      if (search.all_categories) {
        return '{all}'
      } else if (categories) {
        // If less than 5, return all; otherwise, return first 3
        // TODO: provide tooltip to view full list
        return categories.length <= 5 ? categories.join(', ') : `${categories.slice(0,3).join(', ')}, ...`
      }
    },

    formatDate(dateStr) {
      if (dateStr) {
        let date = new Date(dateStr)
        return Intl.DateTimeFormat('en', { dateStyle: "medium", timeStyle: "medium" }).format(date)
      }
      return null
    },

    categoryName(category) {
      return this.categories[category] ? this.categories[category].name : category
    },

    classificationName(classification) {
      if (this.searchResults[this.category] && this.searchResults[this.category][classification]) {
        return this.searchResults[this.category][classification].name
      }
      return classification
    },

    sourceName(sourceId) {
      if (this.searchResultSources[this.classification]) {
        let source = this.searchResultSources[this.classification].find(s => s.id == sourceId)
        return source ? source.name : sourceId
      }
      return sourceId
    },

    getJobStatus(search) {
      return search.job ? search.job.status : "stalled"
    },

    // 
    // -- Network graph nodes
    // 

    // Setup graph spoke nodes based on search results, which may be first-level results across
    // all categories or second-level results across all classifications within a category
    async setupSpokeNodes(category=null) {
      // Clear out spoke nodes on instance and wait for DOM to update; otherwise, the NetworkGraph child component
      // will be updated instead of being unmounted/mounted, leading to rendering issues. 
      this.spokeNodes = []
      await nextTick()
 
      // Identify results set
      let results = this.searchResults || {}
      if (category) {
        results = this.searchResults[category] || {}
      }
      if (_.isEmpty(results)) return
 
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
        // classification, a specific category, or for all categories
        if (category && key == 'total') continue
        let count = category ? obj.count : obj.total.count
        let label = category ? obj.name : this.categories[key].name
        let vizId = key
        // Add node to list
        nodes.push({ 
          name: `${count}`, // displayed on the graph
          nodeId: label, // displayed on the graph
          vizId: vizId, // needed to process click events
          size: this.getNodeSize(count, maxCount),
          color: this.getLabelColor(label),
        })
      }
 
      // Set spoke nodes on instance
      this.spokeNodes = nodes
    },

    getNodeSize(count, maxCount) {
      return this.minNodeSize + (count/maxCount)*this.nodeSizeMultiplier
    },

    //
    // -- Bar chart data
    //

    async setupChartData(classification) {
      // Clear out chart data on instance and wait for DOM to update
      this.chartData = {}
      await nextTick()

      // Identify results set
      let results = {}
      if (classification) {
        results = this.searchResultSources[classification] || {}
      }
      if (_.isEmpty(results)) return

      // Prepare chart data
      let vizIds = []
      let labels = []
      let counts = []
      let colors = []
      for (let result of results) {
        vizIds.push(result.id || result.name)
        labels.push(result.name)
        counts.push(result.count)
        colors.push(this.getLabelColor(result.name))
      }

      // Set chart data on instance
      this.chartData = {
        labels: labels,
        datasets: [
          {
            vizIds: vizIds,
            data: counts,
            backgroundColor: colors,
          },
        ],
      }
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
      this.entries = {}
      this.entry = null
      this.errors = []
      this.setupSpokeNodes()
    },

    async enterClassification(classification) {
      // Set classification on instance; setup spoke nodes to view intra-classification results
      this.classification = classification
      await this.fetchSearchSources(this.search.id, this.category, this.classification)
      this.setupChartData(this.classification)
    },

    exitClassification() {
      // Clear classification on instance; setup spoke nodes to view inter-classification results
      this.classification = null
      this.source = null
      this.entries = {}
      this.entry = null
      this.errors = []
      this.setupSpokeNodes(this.category)
    },

    enterSource(source) {
      this.source = source
      this.fetchSearchEntries(this.search.id, this.category, this.classification, this.source, true)
    },

    exitSource(source) {
      this.source = null
      this.entries = {}
      this.entry = null
      this.errors = []
      this.setupChartData(this.classification)
    },

    async enterEntry(entry) {
      entry.abstract = null
      this.entry = entry
      this.entry.abstract = await this.fetchAbstract(this.entry.scopus_id)
    },

    exitEntry() {
      this.entry = null
      this.errors = []
    },

    // 
    // -- API fetches
    // 

    async fetchSubjectAreaClassifications() {
      let response = await internalGet('/subject-area-classifications?cached=true')
      if (response) {
        this.categories = response.categories
      }
    },

    async fetchSearchResults(opts={}) {
      // Unpack options
      let searchId = opts.searchId || null
      let pending = opts.pending || false
      // Reset state of search results (if we're fetching a specific set of search results)
      if (searchId) this.resetSearchResults()
      // Fetch data
      let response = await internalGet('/search-results' + (searchId ? `/${searchId}` : '') + (pending ? `?pending=true` : ''))
      if (response) {
        if (searchId) {
          this.searchResults = response.results
          this.setupSpokeNodes()
          // TEMP
          // this.enterCategory("MEDI") //MEDI
          // this.enterClassification("2739") //2739
          // this.enterSource(144989)
          // TEMP
        } else if (pending) {
          this.searchesPending = response.results
        } else {
          this.searchesCompleted = response.results
        }
      } else {
        this.errors.push(`Failed to retrieve existing search results`)
      }
    },

    async startSearch(query, categories=null) {
      // Fetch data
      let data = {query: query, categories: categories} // if categories is null, all categories will be searched
      let response = await internalPost('/search', data)
      if (response) {
        this.searchesPending.unshift(response.search)
      } else {
        this.errors.push(`Failed to retrieve new search results`)
      }
    },

    async restartSearch(searchId) {
      // Restart stalled search
      let response = await internalPost(`/search/${searchId}/restart`, {})
      if (response) {
        this.searchesPending = this.searchesPending.map(search => {
          return (search.id == searchId) ? response.search : search
        })
      } else {
        this.errors.push(`Failed to retrieve new search results`)
      }
    },

    async fetchSearchSources(searchId, category, classification) {
      // Fetch data
      let response = await internalGet(`/search-results/${searchId}/sources?category=${category}&classification=${classification}`)
      if (response) {
        let results = response.results || []
        this.searchResultSources = {
            ...this.searchResultSources,
            [classification]: results.sort((a,b) => b.count - a.count).slice(0,500) // We can only chart so many data points
        }
      } else {
        this.errors.push(`Failed to retrieve sources`)
      }
    },

    async fetchSearchEntries(searchId, category, classification, source, reset=false) {
      const offset = reset ? 0 : this.entriesOffset
      // Fetch data
      let url = `/search-results/${searchId}/entries?category=${category}&classification=${classification}&source=${source}&limit=${LIMIT}&offset=${offset}`
      let response = await internalGet(url)
      if (response) {
        // TODO: comment
        if (reset || !this.entries[classification]) {
          this.entries = {...this.entries, [classification]: response.results}
        } else {
          this.entries = {...this.entries, [classification]: [...this.entries[classification], ...response.results]}
        }
        this.entriesCount = response.count
        this.entriesOffset += LIMIT
      } else {
        this.errors.push(`Failed to retrieve entries`)
      }
    },

    async fetchMoreSearchEntries() {
      this.fetchSearchEntries(this.search.id, this.category, this.classification, this.source, false)
    },

    async fetchAbstract(scopusId) {
      // Fetch data
      let response = await internalGet(`/abstract/${scopusId}`)
      if (response && response.abstract) {
        return response.abstract
      } else {
        this.errors.push(`Failed to retrieve abstract`)
      }
    }
  },
})

app.use(VNetworkGraph)
app.mount('#visualizer')
