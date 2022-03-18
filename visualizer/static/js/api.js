const apiDebug = appDebug // global JS variable from base template

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
  if (apiDebug) console.log('internalGet():', url)

  // Make GET request
  let response = await $.ajax({
    type: 'GET',
    url: url,
    headers: _assembleHeaders(),
    success: function(data) {
      if (apiDebug) console.log('internalGet(): SUCCESS:', url, data)
      return data
    },
    error: function(error) {
      console.error('internalGet(): ERROR:', url, error)
      return null
    },
    dataType: 'json',
    contentType : 'application/json'
  });

  return response
}

export async function internalPost(url, payload) {
  if (apiDebug) console.log('internalPost():', url)
  payload.csrfmiddlewaretoken = Cookies.get('csrftoken')

  // Make POST request
  let response = await $.ajax({
    type: 'POST',
    url: url,
    data: JSON.stringify(payload),
    headers: _assembleHeaders(),
    success: function(data) {
      if (apiDebug) console.log('internalPost(): SUCCESS:', url, data)
      return data
    },
    error: function(error) { 
      console.error('internalPost(): ERROR:', url, error)
      return null
    },
    dataType: 'json',
    contentType : 'application/json'
  });

  return response
}
