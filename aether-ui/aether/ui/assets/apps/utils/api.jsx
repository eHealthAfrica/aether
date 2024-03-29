/*
 * Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { LOGOUT_URL } from './constants'
import { NotFoundError, HTTPError } from './errors'

const HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete']

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

export default class ApiClient {
  constructor () {
    HTTP_METHODS.forEach(method => {
      this[method] = (path, headers, { params, data } = {}) => {
        const csrfToken = (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value
        const initialHeaders = {
          'X-CSRFToken': csrfToken,
          // The default behaviour of Kong is to redirect to the login page
          // if the user is not authorized, with this header we try to receive
          // the real status code "401" and redirect us to the logout page
          'X-Oauth-Unauthorized': 'status_code'
        }
        const options = {
          method,
          credentials: 'same-origin',
          headers: Object.assign(initialHeaders, headers),
          body: JSON.stringify(data)
        }

        const host = window.location.origin + window.location.pathname
        const url = host + appendParams(path, params).substring(1)

        return new Promise((resolve, reject) => {
          window.fetch(url, options)
            .then(response => {
              if (response.ok) {
                // `DELETE` method returns a 204 status code without response content
                if (response.status === 204) {
                  return resolve() // NO-CONTENT response
                }

                return response.json()
                  .then(content => { resolve(content) })
                  // Should be extended to cater for content-types other than json
                  .catch(error => { reject(error) })
              } else {
                const defaultError = new HTTPError(response.statusText, response, response.status)

                if (response.status === 401 || response.status === 403) {
                  // 401 - Unauthorized / 403 - Forbidden
                  // redirect to logout
                  return window.location.assign(host + LOGOUT_URL)
                }

                if (response.status === 404) {
                  return reject(new NotFoundError('Resource Not Found'))
                }

                if (!response.body) {
                  return reject(defaultError)
                }

                response.json()
                  .then(error => { reject(new HTTPError(error.detail, error, response.status)) })
                  // Should be extended to cater for content-types other than json
                  .catch(() => { reject(defaultError) })
              }
            })
            .catch(err => { reject(err) })
        })
      }
    })
  }
}
