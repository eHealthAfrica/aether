/* global jQuery */
import 'whatwg-fetch'
import { NotFoundError } from './errors'

const methods = ['get', 'post', 'put', 'patch', 'del']

export default class ApiClient {
  constructor (req) {
    methods.forEach(method => {
      this[method] = (path, headers, { params, data } = {}) => {
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
          headers: Object.assign({ 'X-CSRFToken': csrfToken }, headers),
          body: JSON.stringify(data)
        }
        path = appendParams(path, params)
        return new Promise((resolve, reject) => {
          window.fetch(path, options)
            .then(res => {
              if (res.status >= 200 && res.status < 400) {
                res.json().then(res => resolve(res)).catch(err => reject(err)) // Should be extended to cater for other content-types or than json
              } else {
                if (res.status === 404) {
                  reject(new NotFoundError())
                } else {
                  res.json().then(error => {
                    resolve({ error, status: res.status })
                  })
                }
              }
            })
            .catch(err => {
              reject(err)
            })
        })
      }
    })
  }
}
