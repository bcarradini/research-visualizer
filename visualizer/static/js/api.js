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
  try {
    return await $.ajax({
      type: 'GET',
      url: url,
      headers: _assembleHeaders(),
      dataType: 'json',
      contentType : 'application/json',
    })
    .done(function(data) {
      if (apiDebug) console.log('internalGet(): SUCCESS:', url, data)
      return data
    })
  } catch (error) {
    console.error('internalGet(): ERROR:', url, error)
  }
}

export async function internalPost(url, payload) {
  if (apiDebug) console.log('internalPost():', url)
  payload.csrfmiddlewaretoken = Cookies.get('csrftoken')

  // Make POST request
  try {
    return await $.ajax({
      type: 'POST',
      url: url,
      data: JSON.stringify(payload),
      headers: _assembleHeaders(),
      dataType: 'json',
      contentType : 'application/json',
    })
    .done(function(data) {
      if (apiDebug) console.log('internalPost(): SUCCESS:', url, data)
      return data
    })
  } catch (error) {
    console.error('internalPost(): ERROR:', url, error)
  }
}

export async function internalDelete(url) {
  if (apiDebug) console.log('internalDelete():', url)

  // Make DELETE request
  try {
    return await $.ajax({
      type: 'DELETE',
      url: url,
      headers: _assembleHeaders(),
      dataType: 'json',
      contentType : 'application/json',
    })
    .done(function(data) {
      if (apiDebug) console.log('internalDelete(): SUCCESS:', url, data)
      return data
    })
  } catch (error) {
    console.error('internalDelete(): ERROR:', url, error)
  }
}
