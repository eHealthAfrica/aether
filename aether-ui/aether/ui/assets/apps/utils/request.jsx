import 'whatwg-fetch'
import jQuery from 'jquery'

/*
* Given a Blob or File object, triggers a file download by creating
* a link object and simulating a click event.
*/
const download = (fileName, url, content) => {
  const a = document.createElement('a')
  document.body.appendChild(a)
  a.style = 'display: none'
  a.download = fileName
  a.href = window.URL.createObjectURL(content)
  a.click()
  window.URL.revokeObjectURL(url)
}

/*
* Takes a URL string and an { name: value } mapping of query parameters,
* and appends the parameters to the URL => https://localhost/?name=value
* Respects existing query parameters in the URL string.
*/
const appendParams = (url, params) => {
  if (!params || Object.keys(params).length === 0) {
    return url
  }

  const queryString = Object.keys(params)
    .filter(key => (
      params[key] !== undefined &&
      params[key] !== null &&
      params[key].toString().trim() !== ''
    ))
    .map(key => [encodeURIComponent(key), encodeURIComponent(params[key])])
    .map(([name, value]) => `${name}=${value}`)
    .join('&')

  if (queryString === '') {
    return url
  }

  return url + (url.includes('?') ? '&' : '?') + queryString
}

const request = (
  method, //                  GET, POST, PUT, PATCH, DELETE
  url, //                     server url
  // rest of options
  {
    params = {}, //           the list of parameters to add to the url
    payload = null, //        in case of POST, PUT, PATCH the payload
    multipart = false, //     in case of POST, PUT, PATCH indicates if sent as FormData
    blob = false, //          indicates if returns a file not a json
    fileName = 'download' //  in case of "blob" the file name
  }
) => {
  const inspectResponse = (response) => {
    // According to fetch docs: https://github.github.io/fetch/
    // Note that the promise won't be rejected in case of HTTP 4xx or 5xx server responses.
    // The promise will be resolved just as it would be for HTTP 2xx.
    // Inspect the response.ok property within the resolved callback
    // to add conditional handling of server errors to your code.

    if (response.ok) {
      // `DELETE` method returns a 204 status code without response content
      if (response.status === 204) {
        return {} // NO-CONTENT response
      }

      // file to download
      if (blob) {
        return response
          .blob()
          .then(download.bind(null, fileName, url))
      }

      const contentType = response.headers.get('Content-Type')
      if (contentType === 'application/json') {
        return response.json()
      }

      return response.text()
    } else {
      const error = new Error(response.statusText)
      error.response = response
      throw error
    }
  }

  // See: https://docs.djangoproject.com/en/1.11/ref/csrf/
  const csrfToken = jQuery('[name=csrfmiddlewaretoken]').val()
  const options = {
    method,
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': csrfToken,
      'X-METHOD': method // See comment below
    }
  }

  if (payload) {
    if (multipart) {
      /* global FormData */
      const formData = new FormData()
      formData.append('csrfmiddlewaretoken', csrfToken)
      Object.keys(payload).forEach(key => {
        const value = payload[key]
        if (value !== null && value !== undefined) {
          if (Array.isArray(value)) {
            value.forEach(val => {
              formData.append(key, val)
            })
          } else {
            formData.append(key, value)
          }
        }
      })
      options.body = formData
      /*
        Fixes:
          django.http.request.RawPostDataException:
            You cannot access body after reading from request's data stream

        Django does not read twice the `request.body` on POST calls;
        but it is read while checking the CSRF token.
        This raises an exception in our ProxyTokenView.
        We are trying to skip it by changing the method from `POST` to `PUT`
        and the ProxyTokenView handler will change it back again.
      */
      if (method === 'POST') {
        options.method = 'PUT'
      }
    } else {
      options.headers['Content-Type'] = 'application/json'
      options.body = JSON.stringify(payload)
    }
  }

  return window
    .fetch(appendParams(url, params), options)
    .then(inspectResponse)
}

export const deleteData = (url, opts = {}) => (
  request('DELETE', url, opts)
)
export const getData = (url, opts = {}) => (
  request('GET', url, opts)
)
export const postData = (url, payload, opts = {}) => (
  request('POST', url, {...opts, payload})
)
export const putData = (url, payload, opts = {}) => (
  request('PUT', url, {...opts, payload})
)
export const patchData = (url, payload, opts = {}) => (
  request('PATCH', url, {...opts, payload})
)

/*
 * The expected list format is:
 *  [
 *    {
 *      name: 'string',
 *      url: 'url string',
 *      opts: { ... }
 *    },
 *    ...
 *  ]
 *
 * Returns an object where each key is the name defined for
 * each entry and the value is the response content.
 */
export const fetchUrls = (list) => Promise
  .all(list.map(item => getData(item.url, item.opts)))
  .then(responses => responses.reduce((acc, response, index) => {
    return {...acc, [list[index].name]: response}
  }, {}))
