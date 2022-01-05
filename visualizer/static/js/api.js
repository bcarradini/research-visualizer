
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
    // let response = await Vue.http.get(url)
    //     .then(response => {
    //         if (!response.ok) throw response
    //         if (DEBUG) console.log('internalGet(): SUCCESS:', url, response)
    //         return response.body
    //     })
    //     .catch(error => {
    //         console.error('internalGet(): ERROR:', url, error)
    //         return null
    //     })
    console.log('TEMP: internalGet(): url =', url)
    let response = await $.get(url, data => {
        console.log('TEMP: internalGet(): data =', data)
        return data
    });
    // TODO: handle failures
    return response
}

export async function internalPost(url, payload) {
    // let response = await Vue.http.post(url, payload, {headers: _assembleHeaders()})
    //     .then(response => {
    //         if (!response.ok) throw response
    //         if (DEBUG) console.log('internalPost(): SUCCESS:', url, response)
    //         return response.body || response.ok
    //     })
    //     .catch(error => {
    //         console.error('internalPost(): ERROR:', url, error)
    //         return null
    //     })
    console.log('TEMP: internalPost(): url =', url)
    payload.csrfmiddlewaretoken = Cookies.get('csrftoken')
    console.log('TEMP: internalPost(): payload =', payload)
    // let response = await $.post(url, payload, data => {
    //     console.log('TEMP: internalPost(): response =', response)        
    //     return data
    // }, 'json')
    let response = await $.ajax({
      type: "POST",
      url: url,
      data: JSON.stringify(payload),
      headers: _assembleHeaders(),
      success: function(data) { return data },
      error: function(error) { 
          console.error('internalPost(): ERROR:', url, error)
          return null
      },
      dataType: "json",
      contentType : "application/json"
    });

    // TODO: handle failures
    return response
}
