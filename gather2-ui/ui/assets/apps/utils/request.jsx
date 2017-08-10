import 'whatwg-fetch'
import jQuery from 'jquery'

export function request (method, url, data) {
  function inspectResponse (response) {
    // According to fetch docs: https://github.github.io/fetch/
    // Note that the promise won't be rejected in case of HTTP 4xx or 5xx server responses.
    // The promise will be resolved just as it would be for HTTP 2xx.
    // Inspect the response.status number within the resolved callback
    // to add conditional handling of server errors to your code.

    if (response.ok) {
      // `DELETE` method returns a 204 status code without response content
      if (response.status !== 204) {
        return response.json()
      } else {
        return {} // NO-CONTENT response
      }
    } else {
      const error = new Error(response.statusText)
      error.response = response
      throw error
    }
  }

  const options = {
    method,
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      // See: https://docs.djangoproject.com/en/1.11/ref/csrf/
      'X-CSRFToken': jQuery('[name=csrfmiddlewaretoken]').val()
    }
  }

  if (data) {
    options.body = JSON.stringify(data)
  }

  return window.fetch(url, options).then(inspectResponse)
}

export function deleteData (url) { return request('DELETE', url) }
export function getData (url) { return request('GET', url) }
export function postData (url, data) { return request('POST', url, data) }
export function putData (url, data) { return request('PUT', url, data) }

export function fetchUrls (urls) {
  return Promise
    .all(urls.map((config) => getData(config.url)))
    .then((results) => {
      // Create a payload object where the key is the name defined for
      // the url and the value is the response content.
      const payload = results.reduce((item, response, index) => {
        item[urls[index].name] = response
        return item
      }, {})
      return payload
    })
}

export default request
