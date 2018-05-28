/* global test, expect */
import {generateSchemaName} from './generateSchemaName'

test('generateSchemaName', () => {
  const prefix = 'TestPrefix'
  const generator = generateSchemaName(prefix)
  const schemas = [
    [
      {type: 'enum'},
      {type: 'enum', name: `${prefix}_0`}
    ],
    [
      {type: 'fixed'},
      {type: 'fixed', name: `${prefix}_1`}
    ],
    [
      {type: 'record'},
      {type: 'record', name: `${prefix}_2`}
    ],
    [
      {type: 'int'},
      {type: 'int'}
    ]
  ]
  schemas.map(([input, output]) => {
    generator(input)
    expect(input).toEqual(output)
  })
})
