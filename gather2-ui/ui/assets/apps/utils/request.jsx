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
        if (data[key]) {
          formData.append(key, data[key])
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
      options.method = 'PUT'
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

/*
 * The expected urls format is:
 *  [
 *    {
 *      name: 'string',
 *      url: 'url string'
 *    },
 *    ...
 *  ]
 *
 * Returns an object where each key is the name defined for
 * each url entry and the value is the response content.
 */
export const fetchUrls = (urls) => Promise
  .all(urls.map((config) => getData(config.url)))
  .then((responses) => responses.reduce((payload, response, index) => {
    return {...payload, [urls[index].name]: response}
  }, {}))

export default request
