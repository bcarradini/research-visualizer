
// 
// Internal requests
// 

function _assembleHeaders() {
  return {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-CSRFToken': Cookies.get('csrftoken'),
  }
}


export async function internalGet(url) {
    let response = await Vue.http.get(url)
        .then(response => {
            if (!response.ok) throw response
            if (DEBUG) console.log('internalGet(): SUCCESS:', url, response)
            return response.body
        })
        .catch(error => {
            console.error('internalGet(): ERROR:', url, error)
            return null
        })
    return response
}

export async function internalPost(url, data) {
    let response = await Vue.http.post(url, data, {headers: _assembleHeaders()})
        .then(response => {
            if (!response.ok) throw response
            if (DEBUG) console.log('internalPost(): SUCCESS:', url, response)
            return response.body || response.ok
        })
        .catch(error => {
            console.error('internalPost(): ERROR:', url, error)
            return null
        })
    return response
}
