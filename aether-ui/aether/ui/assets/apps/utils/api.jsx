/* global fetch, jQuery */
const methods = ['get', 'post', 'put', 'patch', 'del']

export default class ApiClient {
  constructor (req) {
    methods.forEach(method => {
      this[method] = (path, headers, { params, data } = {}) =>
        new Promise((resolve, reject) => {
          const csrfToken = jQuery('[name=csrfmiddlewaretoken]').val()
          const appendParams = (path, params) => {
            if (!params || Object.keys(params).length === 0) {
              return path
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
              return path
            }

            return path + (path.includes('?') ? '&' : '?') + queryString
          }

          const options = {
            method,
            credentials: 'same-origin',
            headers: Object.assign({
              'X-CSRFToken': csrfToken,
              'X-METHOD': method
            }, headers),
            body: JSON.stringify(data)
          }
          path = appendParams(path, params)
          fetch(path, options)
            .then(res => res.json()) // Should be extended to cater for other content-types or than json
            .then(res => {
              resolve(res)
            })
            .catch(err => reject(err))
        })
    })
  }
}
