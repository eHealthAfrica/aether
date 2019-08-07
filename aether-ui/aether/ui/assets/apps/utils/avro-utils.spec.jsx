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

/* global describe, expect, it */

import * as utils from './avro-utils'

describe('AVRO utils', () => {
  describe('deriveEntityTypes', () => {
    it('derives valid entity types from a schema', () => {
      const schemaName = 'Test'
      const schema = {
        name: schemaName,
        type: 'record',
        fields: [
          {
            name: 'a',
            type: 'int'
          },
          {
            name: 'b',
            type: ['null', 'string']
          },
          {
            name: 'c',
            type: ['string', 'int']
          }
        ]
      }

      const result = utils.deriveEntityTypes(schema)

      expect(result[0].fields[0].name).toEqual('a')
      expect(result[0].fields[0].type).toEqual(['null', 'int'])

      expect(result[0].fields[1].name).toEqual('b')
      expect(result[0].fields[1].type).toEqual(['null', 'string'])

      expect(result[0].fields[2].name).toEqual('c')
      expect(result[0].fields[2].type).toEqual(['null', 'string', 'int'])

      expect(result[0].fields[3].name).toEqual('id')
      expect(result[0].fields[3].type).toEqual('string')
    })
  })

  describe('deriveMappingRules', () => {
    it('derives valid mapping rules from a schema', () => {
      const schemaName = 'Test'
      const schema = {
        name: schemaName,
        type: 'record',
        fields: [
          {
            name: 'a',
            type: 'string'
          },
          {
            name: 'b',
            type: 'int'
          }
        ]
      }
      const expected = [
        {
          source: '$.a',
          destination: `${schemaName}.a`
        },
        {
          source: '$.b',
          destination: `${schemaName}.b`
        }
      ]

      const result = utils.deriveMappingRules(schema)

      expected.map((mappingRule, i) => {
        expect(mappingRule.source).toEqual(result[i].source)
        expect(mappingRule.destination).toEqual(result[i].destination)
      })
      expect(result[2].source).toEqual('#!uuid')
      expect(result[2].destination).toEqual('Test.id')
    })
  })

  describe('traverseObject', () => {
    it('traverses object and applies a function to each node', () => {
      const result = []
      const f = (node) => { result.push(node) }
      const input = { a: [1, { b: [2, 3] }] }
      utils.traverseObject(f, input)
      const expected = [
        { a: [1, { b: [2, 3] }] },
        [1, { b: [2, 3] }],
        1,
        { b: [2, 3] },
        [2, 3],
        2,
        3
      ]
      expect(expected).toEqual(result)
    })
  })

  describe('generateSchemaName', () => {
    it('should generate valid schema names', () => {
      const prefix = 'TestPrefix'
      const generator = utils.generateSchemaName(prefix)
      const schemas = [
        [
          { type: 'enum' },
          { type: 'enum', name: `${prefix}_0` }
        ],
        [
          { type: 'fixed' },
          { type: 'fixed', name: `${prefix}_1` }
        ],
        [
          { type: 'record' },
          { type: 'record', name: `${prefix}_2` }
        ],
        [
          { type: 'int' },
          { type: 'int' }
        ]
      ]
      schemas.map(([input, output]) => {
        generator(input)
        expect(input).toEqual(output)
      })
    })
  })

  describe('generateSchema', () => {
    it('should generate a valid avro schema', () => {
      const input = { a: [{ b: 1 }, { c: 1 }] }
      const expected = {
        type: 'record',
        fields: [
          {
            name: 'a',
            type: {
              type: 'array',
              items: {
                type: 'record',
                fields: [
                  {
                    name: 'b',
                    type: ['null', 'int']
                  },
                  {
                    name: 'c',
                    type: ['null', 'int']
                  }
                ],
                name: 'Auto_1'
              }
            }
          }
        ],
        name: 'Auto_0'
      }
      const result = utils.generateSchema(input)
      expect(expected).toEqual(result)
    })
  })

  describe('isOptionalType', () => {
    it('should return false if type is not a union', () => {
      expect(utils.isOptionalType({ type: 'array', items: 'another_type' })).toBeFalsy()
      expect(utils.isOptionalType({ type: 'record' })).toBeFalsy()
      expect(utils.isOptionalType({ type: 'map' })).toBeFalsy()
      expect(utils.isOptionalType('null')).toBeFalsy()
      expect(utils.isOptionalType({ type: 'null' })).toBeFalsy()
    })

    it('should return true only if type is a union of at least two elements, one of them "null" and another not', () => {
      expect(utils.isOptionalType(['boolean', 'int'])).toBeFalsy()
      expect(utils.isOptionalType(['float', { type: 'enum' }])).toBeFalsy()
      expect(utils.isOptionalType(['string', 'int', { type: 'record' }])).toBeFalsy()
      expect(utils.isOptionalType(['null', { type: 'null' }])).toBeFalsy()

      expect(utils.isOptionalType(['null', 'int'])).toBeTruthy()
      expect(utils.isOptionalType(['null', { type: 'enum' }])).toBeTruthy()
      expect(utils.isOptionalType(['null', 'int', { type: 'record' }])).toBeTruthy()
    })
  })

  describe('isPrimitive', () => {
    it('should flag basic primitives as primitives', () => {
      expect(utils.isPrimitive('null')).toBeTruthy()
      expect(utils.isPrimitive('boolean')).toBeTruthy()
      expect(utils.isPrimitive('int')).toBeTruthy()
      expect(utils.isPrimitive('long')).toBeTruthy()
      expect(utils.isPrimitive('float')).toBeTruthy()
      expect(utils.isPrimitive('double')).toBeTruthy()
      expect(utils.isPrimitive('bytes')).toBeTruthy()
      expect(utils.isPrimitive('string')).toBeTruthy()
      expect(utils.isPrimitive('enum')).toBeTruthy()
      expect(utils.isPrimitive('fixed')).toBeTruthy()

      expect(utils.isPrimitive({ type: 'null' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'boolean' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'int' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'long' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'float' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'double' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'bytes' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'string' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'enum' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'fixed' })).toBeTruthy()
    })

    it('should detect complex types', () => {
      expect(utils.isPrimitive({ type: 'array', items: 'another_type' })).toBeFalsy()
      expect(utils.isPrimitive({ type: 'record' })).toBeFalsy()
      expect(utils.isPrimitive({ type: 'map' })).toBeFalsy()
    })

    it('should flag as primitive certain complex types', () => {
      expect(utils.isPrimitive(['null', 'int'])).toBeTruthy()
      expect(utils.isPrimitive(['null', 'int', 'string'])).toBeTruthy()
      expect(utils.isPrimitive(['null', { type: 'enum' }])).toBeTruthy()
      expect(utils.isPrimitive(['null', 'int', { type: 'record' }])).toBeFalsy()

      expect(utils.isPrimitive({ type: 'array', items: 'long' })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'array', items: ['null', 'boolean', 'long'] })).toBeTruthy()
      expect(utils.isPrimitive({ type: 'array', items: { type: 'map' } })).toBeFalsy()
    })
  })

  describe('typeToString', () => {
    it('should keep basic types', () => {
      expect(utils.typeToString('null')).toEqual('null')
      expect(utils.typeToString('any')).toEqual('any')

      expect(utils.typeToString({ type: 'null' })).toEqual('null')
      expect(utils.typeToString({ type: 'any' })).toEqual('any')
    })

    it('should detect nullable types', () => {
      expect(utils.typeToString(['null', 'int'])).toEqual('int (nullable)')
      expect(utils.typeToString(['null', { type: 'enum' }])).toEqual('enum (nullable)')

      expect(utils.typeToString(['null', 'int', { type: 'record' }]))
        .toEqual('int, record (nullable)')

      expect(utils.typeToString(['null', 'int'], '(null)', true)).toEqual('int (null)')
      expect(utils.typeToString(['null', { type: 'enum' }], '(null)', true)).toEqual('enum (null)')
      expect(utils.typeToString(['null', 'int', { type: 'record' }], '(null)', true))
        .toEqual('union (null)')
    })

    it('should detect array types', () => {
      expect(utils.typeToString({ type: 'array', items: 'another_type' }))
        .toEqual('array [another_type]')
      expect(utils.typeToString({ type: 'array', items: ['null', 'boolean', 'long'] }))
        .toEqual('array [boolean, long (nullable)]')
      expect(utils.typeToString({ type: 'array', items: ['null', 'boolean', { type: 'record' }] }))
        .toEqual('array [boolean, record (nullable)]')
    })

    it('should detect map types', () => {
      expect(utils.typeToString({ type: 'map', values: 'another_type' }))
        .toEqual('map {another_type}')
      expect(utils.typeToString({ type: 'map', values: ['null', 'boolean', 'long'] }))
        .toEqual('map {boolean, long (nullable)}')
      expect(utils.typeToString({ type: 'map', values: ['null', 'boolean', { type: 'record' }] }))
        .toEqual('map {boolean, record (nullable)}')
    })

    it('should detect complex types', () => {
      expect(utils.typeToString({
        type: 'array',
        items: [
          'null',
          { type: 'map', values: ['null', 'int', { type: 'record' }] }
        ]
      }))
        .toEqual('array [map {int, record (nullable)} (nullable)]')
    })
  })
})
