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

import { generateGUID } from './index'

// In-house workaround to the avsc library to avoid null values
// in case of union types
avro.types.UnwrappedUnionType.prototype.random = function () {
  const types = this.types.filter(({ typeName }) => typeName !== 'null')
  if (types.length === 0) {
    return null
  }
  const index = Math.floor(Math.random() * types.length)
  return types[index].random()
}

export const parseSchema = (schema) => (
  avro.parse(schema, { noAnonymousTypes: true, wrapUnions: false })
)

export const isOptionalType = (type) => {
  return Array.isArray(type) && (type.indexOf('null') > -1)
}

export const makeOptionalType = (type) => {
  if (isOptionalType(type)) {
    return type
  }
  if (Array.isArray(type)) {
    return ['null', ...type]
  }
  return ['null', type]
}

export const makeOptionalField = (field) => {
  // The top-level "id" field is reserved for unique ids; do not make it
  // optional.
  if (field.name === 'id') { return field }
  return { ...field, type: makeOptionalType(field.type) }
}

export const deriveEntityTypes = (schema) => {
  const fields = schema.fields.map(makeOptionalField)
  if (!fields.find(field => field.name === 'id')) {
    // DETECTED CONFLICT
    // the "id" must be an string if the schema defines it with another type
    // the validation could fail
    // this step only includes it if missing but does not change its type to "string"
    fields.push({
      name: 'id',
      type: 'string'
    })
  }
  return [{ ...schema, fields }]
}

export const deriveMappingRules = (schema) => {
  const fieldToMappingRule = (field) => {
    return {
      id: generateGUID(),
      source: `$.${field.name}`,
      destination: `${schema.name}.${field.name}`
    }
  }
  const rules = schema.fields.map(fieldToMappingRule)

  if (!schema.fields.find(field => field.name === 'id')) {
    rules.push({
      id: generateGUID(),
      source: `#!uuid`,
      destination: `${schema.name}.id`
    })
  }
  return rules
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

export const generateSchema = (obj, defaultName = 'Auto') => {
  const schema = avro.Type.forValue(obj).schema()
  const nameGen = generateSchemaName(defaultName)
  traverseObject(nameGen, schema)
  return schema
}
