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

import avro from 'avsc'

import { generateGUID } from './index'
import { AVRO_EXTENDED_TYPE } from './constants'

// AVRO types:
// - primitive: null, boolean, int, long, float, double, bytes, string
// - complex: record, map, array, union, enum, fixed
const NULL = 'null'
const PRIMITIVE_TYPES = [
  // {"type": "aaa", "name": "a", doc: "b", ...}
  NULL,
  'boolean',
  'int',
  'long',
  'float',
  'double',
  'bytes',
  'string',

  // these ones are not primitives but work the same
  // {"type": {"type": "enum", "name": "e", "symbols": ["A", "B", "C", "D"]}}
  'enum',
  // {"type": {"type": "fixed", "size": 16, "name": "f"}}
  'fixed'
]
export const FIELD_ID = 'id'

// In-house workaround to the avsc library to avoid null values
// in case of union types
avro.types.UnwrappedUnionType.prototype.random = function () {
  const types = this.types.filter(({ typeName }) => typeName !== NULL)
  if (types.length === 0) {
    return null
  }
  const index = Math.floor(Math.random() * types.length)
  return types[index].random()
}

const randomBytes = (len = 8) => Math.floor((1 + Math.random()) * 16 ** len).toString(16).slice(1)

// In-house workaround to the avsc library to avoid buffer serialization
avro.types.FixedType.prototype.random = function () {
  return randomBytes(this.size)
}
avro.types.BytesType.prototype.random = function () {
  return randomBytes()
}

export const parseSchema = (schema) => (
  avro.parse(schema, { noAnonymousTypes: true, wrapUnions: false })
)

export const randomInput = (schema) => {
  const type = parseSchema(schema)
  const input = type.random()

  // check if there is a string "id" field
  if (schema.fields.find(field => field.name === FIELD_ID && field.type === 'string')) {
    input[FIELD_ID] = generateGUID() // make it more UUID
  }
  return input
}

/**
 * Indicates if the given AVRO type corresponds to a "nullable" type
 *
 * @param {*} type   - The AVRO type
 *
 * @return {boolean} - true if type is a union type and one of the options is "null"
 *                     Otherwise false
 */
export const isOptionalType = (type) => (
  Array.isArray(type) &&
  type.filter(v => (v.type || v) === NULL).length > 0 &&
  type.filter(v => (v.type || v) !== NULL).length > 0
)

/**
 * Converts the given AVRO type into a "nullable" type
 *
 * @param {*} type   - The AVRO type
 *
 * @return {array}   - Array of AVRO types, one of the entries is "null".
 */
export const makeOptionalType = (type) => (
  isOptionalType(type) ? type : [NULL, ...(Array.isArray(type) ? type : [type])]
)

/**
 * Converts the given AVRO field into a "nullable" field
 *
 * @param {object} field   - The AVRO field
 *
 * @return {object}        - The same AVRO field but its "type" is an array of
 *                           AVRO types, one of the entries is "null".
 */
export const makeOptionalField = (field) => (
  // The top-level "id" field is reserved for unique ids; do not make it optional.
  (field.name === FIELD_ID) ? field : { ...field, type: makeOptionalType(field.type) }
)

/**
 * Indicates if the given AVRO type corresponds to a "primitive" type
 *
 * @param {*} type   - The AVRO type
 *
 * @return {boolean} - true if type is
 *                       - primitive or
 *                       - array of primitives or
 *                       - "nullable" primitive
 *                     Otherwise false
 *                       - record
 *                       - map
 *                       - tagged union
 */
export const isPrimitive = (type) => (
  // Real primitives: {"type": "aaa"}
  PRIMITIVE_TYPES.indexOf(type) > -1 ||
  // Complex types but taken as primitives: {"type": {"type": "zzz"}}
  (type.type && isPrimitive(type.type)) ||
  // array of primitives
  (type.type === 'array' && isPrimitive(type.items)) ||
  // union of primitives
  (Array.isArray(type) && type.filter(isPrimitive).length === type.length)
)

export const typeToString = (type, nullable = '(nullable)', short = false, extended = null) => {
  const flat = (a) => Array.isArray(a) && a.length === 1 ? a[0] : a
  const clean = (type) => flat(
    !isOptionalType(type) ? type : type.filter(v => (v.type || v) !== NULL)
  )

  const suffix = isOptionalType(type) ? ' ' + nullable : ''
  const cleanType = clean(type)
  const t = flat((cleanType && (cleanType[AVRO_EXTENDED_TYPE] || cleanType.type)) || cleanType)

  const typeStr = Array.isArray(t) ? 'union' : extended || t
  let childrenStr = ''
  switch (t) {
    case 'enum':
      childrenStr = ` (${cleanType.symbols.join(', ')})`
      break

    case 'map':
      childrenStr = ` {${typeToString(cleanType.values, nullable, short, cleanType[AVRO_EXTENDED_TYPE])}}`
      break

    case 'array':
      childrenStr = ` [${typeToString(cleanType.items, nullable, short, cleanType[AVRO_EXTENDED_TYPE])}]`
      break

    default:
      if (Array.isArray(t)) {
        childrenStr = !short || isPrimitive(t)
          ? ': ' + t.map(v => typeToString(v, nullable, short)).join(', ')
          : ''
      }
  }
  return `${typeStr}${childrenStr}${suffix}`
}

export const deriveEntityTypes = (schema, schemaName = null) => {
  const fields = schema.fields.map(makeOptionalField)
  if (!fields.find(field => field.name === FIELD_ID)) {
    // DETECTED CONFLICT
    // the "id" must be an string if the schema defines it with another type
    // the validation could fail
    // this step only includes it if missing but does not change its type to "string"
    fields.push({
      name: FIELD_ID,
      type: 'string'
    })
  }
  return [{ ...schema, fields, name: schemaName || schema.name }]
}

export const deriveMappingRules = (schema, schemaName = null) => {
  const fieldToMappingRule = (field) => {
    return {
      id: generateGUID(),
      source: `$.${field.name}`,
      destination: `${schemaName || schema.name}.${field.name}`
    }
  }
  const rules = schema.fields.map(fieldToMappingRule)

  if (!schema.fields.find(field => field.name === FIELD_ID)) {
    rules.push({
      id: generateGUID(),
      source: '#!uuid',
      destination: `${schemaName || schema.name}.${FIELD_ID}`
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
    if (typeof obj[k] === 'object' && Object.prototype.hasOwnProperty.call(obj, k)) {
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
