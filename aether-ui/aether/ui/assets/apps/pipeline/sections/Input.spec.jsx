/* global describe, expect, it */
import React from 'react'
import sinon from 'sinon'

import { mountWithIntl } from 'enzyme-react-intl'

import { findByDataQa } from '../../../tests/ui-tests-environment/utils'
import Modal from '../../components/Modal'
import {
  deriveEntityTypes,
  deriveMappingRules,
  IdentityMapping
} from './Input'

describe('deriveEntityTypes', () => {
  it('derives valid entity types from a schema', () => {
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
    const result = deriveEntityTypes(schema)
    console.log(result)
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
    const result = deriveMappingRules(schema)
    expected.map((mappingRule, i) => {
      expect(mappingRule.source).toEqual(result[i].source)
      expect(mappingRule.destination).toEqual(result[i].destination)
    })
  })
})

describe('<IdentityMapping />', () => {
  it('opens modal', () => {
    const component = mountWithIntl(<IdentityMapping />)
    expect(component.find(Modal).length).toEqual(0)
    findByDataQa(component, 'input.identityMapping.btn-apply').simulate('click')
    expect(component.find(Modal).length).toEqual(1)
  })

  it('triggers pipeline updates and closes modal', () => {
    const selectedPipeline = {
      schema: {
        type: 'record',
        name: 'Test',
        fields: [
          {
            name: 'a',
            type: 'string'
          }
        ]
      }
    }
    const updatePipeline = sinon.spy()
    const component = mountWithIntl(
      <IdentityMapping
        selectedPipeline={selectedPipeline}
        updatePipeline={updatePipeline}
      />
    )
    expect(component.find(Modal).length).toEqual(0)
    findByDataQa(component, 'input.identityMapping.btn-apply').simulate('click')
    expect(component.find(Modal).length).toEqual(1)
    findByDataQa(component, 'input.identityMapping.btn-confirm').simulate('click')
    expect(updatePipeline.callCount).toEqual(1)
    const {
      schema,
      mapping,
      entity_types: entityTypes
    } = updatePipeline.args[0][0]
    expect(selectedPipeline.schema)
      .toEqual(schema)
    expect(selectedPipeline.schema.fields.length)
      .toEqual(mapping.length)
    expect(`$.${selectedPipeline.schema.fields[0].name}`)
      .toEqual(mapping[0].source)
    expect(mapping[0].destination)
      .toEqual(
        `${selectedPipeline.schema.name}.${selectedPipeline.schema.fields[0].name}`
      )
    expect(entityTypes.length)
      .toEqual(selectedPipeline.schema.fields.length)
    expect(entityTypes[0])
      .toEqual(selectedPipeline.schema)
    expect(component.find(Modal).length).toEqual(0)
  })
})
