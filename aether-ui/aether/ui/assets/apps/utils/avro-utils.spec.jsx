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

/* global describe, expect, it */

import * as utils from './avro-utils'

describe('AVRO utils', () => {
  describe('makeOptionalField', () => {
    it('makes an AVRO field optional', () => {
      const tests = [
        [
          { name: 'a', type: 'string' },
          { name: 'a', type: ['null', 'string'] }
        ],
        [
          { name: 'b', type: ['null', 'string'] },
          { name: 'b', type: ['null', 'string'] }
        ],
        [
          { name: 'c', type: ['int', 'string'] },
          { name: 'c', type: ['null', 'int', 'string'] }
        ]
      ]

      tests.map(([args, result]) => {
        expect(utils.makeOptionalField(args)).toEqual(result)
      })
    })
  })

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
      let result = []
      const f = (node) => { result.push(node) }
      const input = { a: [1, { b: [2, 3] }] }
      utils.traverseObject(f, input)
      const expected = [
        { 'a': [1, { 'b': [2, 3] }] },
        [1, { 'b': [2, 3] }],
        1,
        { 'b': [2, 3] },
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
})
