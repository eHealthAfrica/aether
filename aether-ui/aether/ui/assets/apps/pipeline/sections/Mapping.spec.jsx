/* global test, expect */
import {deriveMappingRules} from './Mapping'

test('deriveMappingRules', () => {
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
  const result = deriveMappingRules(schema)
  expected.map((mappingRule, i) => {
    expect(mappingRule.source).toEqual(result[i].source)
    expect(mappingRule.destination).toEqual(result[i].destination)
  })
})
