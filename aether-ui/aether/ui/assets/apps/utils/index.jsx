/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

/**
 * Clones object.
 *
 * @param {*} x -- the object
 */
export const clone = (x) => JSON.parse(JSON.stringify(x))

/**
 * Generates random UUID
 */
export const generateGUID = () => {
  const s4 = () => {
    return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1)
  }
  return `${s4()}${s4()}-${s4()}-${s4()}-${s4()}-${s4()}${s4()}${s4()}`
}

/**
 * Checks if the two objects are equal, comparing even nested properties.
 *
 * @param {*}      a          -- object 1
 * @param {*}      b          -- object 2
 * @param {bool}   ignoreNull -- ignore null values
 */
export const deepEqual = (a, b, ignoreNull = false) => {
  // Note:
  //   [x, y, z,...]  equals to  {'0': x, '1': y, '2': z, ...}
  const getType = (value) => Object.prototype.toString.call(value)

  if (getType(a) !== getType(b)) {
    return false
  }

  if (['[object Object]', '[object Array]'].indexOf(getType(a)) === -1) {
    return a === b
  }

  let ka = Object.keys(a)
  let kb = Object.keys(b)

  // ignore null and undefined values
  if (ignoreNull) {
    ka = ka.filter((x) => a[x] != null)
    kb = kb.filter((x) => b[x] != null)
  }

  // having the same number of owned properties (keys incorporates hasOwnProperty)
  if (ka.length !== kb.length) {
    return false
  }

  // the same set of keys (although not necessarily the same order),
  ka.sort()
  kb.sort()

  // cheap key test
  for (let i = ka.length - 1; i >= 0; i--) {
    if (ka[i] !== kb[i]) {
      return false
    }
  }

  // equivalent values for every corresponding key, and
  // possibly expensive deep test
  for (let i = ka.length - 1; i >= 0; i--) {
    const key = ka[i]
    if (!deepEqual(a[key], b[key], ignoreNull)) {
      return false
    }
  }

  return true
}

/**
 * Indicates if the object is blank.
 *
 * Options:
 *    - "null"
 *    - "undefined"
 *    - blank strings
 *    - empty arrays
 *    - empty objects
 *    - "false" is not blank.
 *
 * @param {*} value -- the object
 */
export const isEmpty = (value) => (
  value === null ||
  value === undefined ||
  JSON.stringify(value) === '{}' ||
  value.toString().trim() === ''
)

/**
 * Replaces the given object in the list, identified by the `id`
 *
 * @param {Array}   list
 * @param {Object}  obj
 */
export const replaceItemInList = (list, obj) => (
  (list || []).map(item => item.id === obj.id ? obj : item)
)

/**
 * Removes the given object in the list, identified by the `id`
 *
 * @param {Array}   list
 * @param {Object}  obj
 */
export const removeItemFromList = (list, obj) => (
  (list || []).filter(item => item.id !== obj.id)
)

/**
 * Takes the logged in user, id (int) and name, from the DOM element
 */
export const getLoggedInUser = () => {
  const loggedInUserElement = document.getElementById('logged-in-user-info')
  return {
    id: parseInt(loggedInUserElement ? loggedInUserElement.getAttribute('data-user-id') : null, 10),
    name: loggedInUserElement ? loggedInUserElement.getAttribute('data-user-name') : ''
  }
}

/**
 * Stringifies the object.
 *
 * @param {*} x -- the object
 */
export const objectToString = (obj) => !isEmpty(obj) ? JSON.stringify(obj, 0, 2) : ''
