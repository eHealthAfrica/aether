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

import avro from 'avsc'

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
  if (typeof a !== 'object') {
    return a === b
  }
  let ka = Object.keys(a)
  let kb = Object.keys(b)
  let key, i
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
  for (i = ka.length - 1; i >= 0; i--) {
    if (ka[i] !== kb[i]) {
      return false
    }
  }
  // equivalent values for every corresponding key, and
  // possibly expensive deep test
  for (i = ka.length - 1; i >= 0; i--) {
    key = ka[i]
    if (!deepEqual(a[key], b[key], ignoreNull)) {
      return false
    }
  }
  return true
}

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
 * Traverse object `obj` and apply function `f` to every node.
 */
export const traverseObject = (f, obj) => {
  f(obj)
  for (var k in obj) {
    if (typeof obj[k] === 'object' && obj.hasOwnProperty(k)) {
      traverseObject(f, obj[k])
    } else {
      f(obj[k])
    }
  }
}

/* This function is applied to all named types in a derived avro record.
 * Background: when `avsc` derives avro schemas from sample data, all
 * records, enums and fixed types will be anonymous.
 * To ensure compatibility with other avro implementations, we need to
 * generate a name for each such type.
 *
 * See: https://github.com/mtth/avsc/issues/108#issuecomment-302436388
 */
export const generateSchemaName = (prefix) => {
  let index = 0
  return (schema) => {
    switch (schema.type) {
      case 'enum':
      case 'fixed':
      case 'record':
        schema.name = `${prefix}_${index++}`
        break
      default:
    }
  }
}

export const generateSchema = (obj) => {
  const schema = avro.Type.forValue(obj).schema()
  const nameGen = generateSchemaName('Auto')
  traverseObject(nameGen, schema)
  return schema
}

export const generateNewContract = (pipeline, newContracts = []) => {
  let existingName = null
  let existingNewName = null
  let count = 0
  let newContractName = ''
  do {
    newContractName = `Contract_${count}`
    existingName = pipeline.contracts.filter(x => x.name === newContractName)
    existingNewName = newContracts.filter(x => x.name === newContractName)
    count++
  } while (existingName.length || existingNewName.length)

  return {
    name: newContractName,
    entity_types: [],
    mapping: [],
    output: {},
    mapping_errors: []
  }
}
