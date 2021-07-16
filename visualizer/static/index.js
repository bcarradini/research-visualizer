
const app = new Vue({
    delimiters: ['${', '}'],
    el: '#vue-el-index',

    data: function() {
        return {
            // URLs
            classificationsUrl: baseUrl+'/subject-area-classifications',
            // TODO: Comment
            query: null,
            lastQuery: null,
            // Scopus data
            categories: [],
            classifications: [],
        }
    },

    created: function () {
        this.fetchSubjectAreaClassifications()
    },

    //
    // -- Methods
    // 

    methods: {
        async fetchSubjectAreaClassifications() {
            let url = this.classificationsUrl
            let response = await Vue.http.get(url) // vue-resource http service
            .then(response => {
                if (!response.ok) throw response
                if (debug) console.log('fetchSubjectAreaClassifications(): SUCCESS:', url, response)
                this.categories = response.body.categories
                this.classifications = response.body.classifications
            })
            .catch(error => {
                console.error('fetchSubjectAreaClassifications(): ERROR:', url, error)
                return null
            })
        },
        search () {
            let query = (this.query || '').trim()
            if (query && query != this.lastQuery) {
                console.log('search!')
                this.lastQuery = query
            } else {
                console.log('no new query :-(')
            }
        }
    },
})
