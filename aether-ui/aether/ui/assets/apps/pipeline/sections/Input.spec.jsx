/* global describe, expect, it, jest */
import React from 'react'

import { mountWithIntl } from 'enzyme-react-intl'

import { findByDataQa } from '../../../tests/ui-tests-environment/utils'
import Modal from '../../components/Modal'
import * as input from './Input'

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
      expect(input.makeOptionalField(args)).toEqual(result)
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
    const result = input.deriveEntityTypes(schema)
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
    const result = input.deriveMappingRules(schema)
    expected.map((mappingRule, i) => {
      expect(mappingRule.source).toEqual(result[i].source)
      expect(mappingRule.destination).toEqual(result[i].destination)
    })
    expect(result[2].source).toEqual('#!uuid')
    expect(result[2].destination).toEqual('Test.id')
  })
})

describe('<IdentityMapping />', () => {
  const pipeline = {
    schema: {
      type: 'record',
      name: 'Test',
      fields: [
        {
          name: 'a',
          type: ['null', 'string']
        }
        // there is no "id" field !!!
      ]
    },
    is_read_only: false
  }

  it('triggers pipeline updates and closes modal', () => {
    const updateContractMock = jest.fn()
    const component = mountWithIntl(
      <input.IdentityMapping
        selectedPipeline={pipeline}
        updateContract={updateContractMock}
      />
    )

    expect(component.find(Modal).length).toEqual(0)
    findByDataQa(component, 'input.identityMapping.btn-apply').simulate('click')
    expect(component.find(Modal).length).toEqual(1)
    findByDataQa(component, 'input.identityMapping.btn-confirm').simulate('click')
    expect(component.find(Modal).length).toEqual(0)

    expect(updateContractMock).toHaveBeenCalledTimes(1)

    const { mapping, entity_types: entityTypes } = updateContractMock.mock.calls[0][0]

    expect(mapping[0].source).toEqual('$.a')
    expect(mapping[0].destination).toEqual('Test.a')

    // added the "id" rule
    expect(mapping[1].source).toEqual('#!uuid')
    expect(mapping[1].destination).toEqual('Test.id')

    expect(entityTypes.length).toEqual(1) // only one Entity Type
    expect(entityTypes[0]).toEqual({
      type: 'record',
      name: 'Test',
      fields: [
        {
          name: 'a',
          type: ['null', 'string']
        },
        {
          name: 'id',
          type: 'string'
        }
      ]
    })
  })

  it('opens modal', () => {
    const component = mountWithIntl(<input.IdentityMapping selectedPipeline={pipeline} />)
    expect(component.find(Modal).length).toEqual(0)
    findByDataQa(component, 'input.identityMapping.btn-apply').simulate('click')
    expect(component.find(Modal).length).toEqual(1)
  })
})
