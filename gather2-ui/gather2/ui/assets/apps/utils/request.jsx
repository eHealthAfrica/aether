import 'whatwg-fetch'
import jQuery from 'jquery'

export const request = (method, url, data = null, multipart = false) => {
  const inspectResponse = (response) => {
    // According to fetch docs: https://github.github.io/fetch/
    // Note that the promise won't be rejected in case of HTTP 4xx or 5xx server responses.
    // The promise will be resolved just as it would be for HTTP 2xx.
    // Inspect the response.ok property within the resolved callback
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
      try {
        error.response = response.json()
      } catch (e) {
        error.response = response
      }
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
      'X-METHOD': method  // See comment below
    }
  }

  if (data) {
    if (multipart) {
      /* global FormData */
      const formData = new FormData()
      formData.append('csrfmiddlewaretoken', csrfToken)
      Object.keys(data).forEach(key => {
        const value = data[key]
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
      options.body = JSON.stringify(data)
    }
  }

  return window.fetch(url, options).then(inspectResponse)
}

export const deleteData = (url) => request('DELETE', url)
export const getData = (url) => request('GET', url)
export const postData = (url, data, multipart = false) => request('POST', url, data, multipart)
export const putData = (url, data, multipart = false) => request('PUT', url, data, multipart)
export const patchData = (url, data, multipart = false) => request('PATCH', url, data, multipart)

/**
 * Request GET from an url, if fails then POST a default object and tries again.
 *
 * Reason: the different apps are connected but they don't know each other.
 * In some cases they should have the same object references but due to their
 * independency it could not always be true. This tries to skip that issue.
 *
 * @param {string} url         - GET url
 * @param {string} forceUrl    - POST url used to create the object below
 * @param {object} defaultData - the default object
 */
export const forceGetData = (url, forceUrl, defaultData) => (
  getData(url)
    // in case of error, try to create it and get again
    .catch(() => postData(forceUrl, defaultData).then(() => getData(url)))
)

/*
 * The expected urls format is:
 *  [
 *    {
 *      name: 'string',
 *      url: 'url string',
 *      // optional, if the request get fails, creates the object below and tries again
 *      force: {
 *        url: 'string',
 *        data: { object }
 *      }
 *    },
 *    ...
 *  ]
 *
 * Returns an object where each key is the name defined for
 * each url entry and the value is the response content.
 */
export const fetchUrls = (urls) => Promise
  .all(urls.map(config => config.force
    ? forceGetData(config.url, config.force.url, config.force.data)
    : getData(config.url)
  ))
  .then(responses => responses.reduce((payload, response, index) => {
    return {...payload, [urls[index].name]: response}
  }, {}))

export default request
