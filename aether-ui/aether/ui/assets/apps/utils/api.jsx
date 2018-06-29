/*
 * Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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

/* global jQuery */
import 'whatwg-fetch'
import { NotFoundError, HTTPError } from './errors'

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
                  reject(new NotFoundError('Resource Not Found'))
                } else {
                  try {
                    res.json().then(err => {
                      const message = err.name && err.name.length && err.name[0]
                      reject(new HTTPError(message, err, res.status))
                    })
                  } catch (err) {
                    reject(err)
                  }
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
