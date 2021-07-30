
// Internal
import {internalGet, internalPost} from './api.js'

const app = new Vue({
    delimiters: ['${', '}'],
    el: '#vue-el-index',

    data: function() {
        return {
            // Queries
            query: null,
            lastQuery: null,
            results: {},
            loadingResults: false,
            // Scopus data
            categories: [],
            classifications: [],
        }
    },

    //
    // -- Lifecycle hooks
    //

    created: function () {
        this.fetchSubjectAreaClassifications()
    },

    // 
    // -- Computed properties
    // 

    computed: {
        loadingPage() {
            return this.categories.length == 0
        }
    },

    //
    // -- Methods
    // 

    methods: {
        async fetchSubjectAreaClassifications() {
            let response = await internalGet('/subject-area-classifications')
            if (response) {
                this.categories = response.categories
                this.classifications = response.classifications                
            }
        },

        async fetchSearchResults(query, categories=[]) {
            this.loadingResults = true
            let data = {query: query, categories: categories.length ? categories : this.categories}
            let response = await internalPost('/search', data)
            if (response) {
                this.results = response.results
            }
            this.loadingResults = false
        },

        search () {
            let query = (this.query || '').trim()
            if (query && query != this.lastQuery) {
                // TEMP
                let categories = this.categories.slice(0, 2)
                // TEMP
                this.fetchSearchResults(query, categories)
                this.lastQuery = query
            }
        }
    },
})
