/* global describe, it, expect */

import React from 'react'
import mockEntityTypesSchema from '../mock/schema_entityTypes.mock'
import { EntityTypeViewer } from '../components'
import { mountWithIntl } from '../../tests/test-react-intl'

describe('EntityTypeViewer', () => {
  it('should take a valid json list of schemas and render entity visualizers', () => {
    const component = mountWithIntl(<EntityTypeViewer schema={JSON.stringify(mockEntityTypesSchema)} />)
    expect(component.find('div.entity-types-schema').children().length).toEqual(2)
    expect(component.html()).not.toContain('Invalid JSON')
    expect(component.html()).not.toContain('Invalid entity type')
    expect(component.html()).not.toContain('Invalid schema')
  })

  it('should take a valid json with empty entities', () => {
    const validJSONWithEmptyObjects = [{}, {}, {}]
    const component = mountWithIntl(<EntityTypeViewer schema={JSON.stringify(validJSONWithEmptyObjects)} />)
    expect(component.find('div.entity-types-schema').children().length).toEqual(3)
    expect(component.html()).toContain('Invalid entity type')
  })

  it('should take an invalid schema and render error', () => {
    const inValidSchema = []
    const component = mountWithIntl(<EntityTypeViewer schema={JSON.stringify(inValidSchema)} />)
    expect(component.html()).toContain('Invalid schema')
  })

  it('should take an empty schema input and render message', () => {
    const component = mountWithIntl(<EntityTypeViewer />)
    expect(component.html()).toContain('No Entity Types added to your pipeline yet.')
  })

  it('should take entity type without fields', () => {
    const entityTypeWithoutProperties = [{name: 'test-name', type: 'record', fields: []}]
    const component = mountWithIntl(<EntityTypeViewer schema={JSON.stringify(entityTypeWithoutProperties)} />)
    expect(component.html()).toContain('Entity has no properties')
  })

  it('should take an invalid JSON and render error message', () => {
    const component = mountWithIntl(<EntityTypeViewer schema={`${JSON.stringify(mockEntityTypesSchema)},`} />)
    expect(component.html()).toContain('Invalid JSON')
  })

  it('should render type name if symbols are missing', () => {
    const entityTypeWithoutSymbols = [...mockEntityTypesSchema]
    entityTypeWithoutSymbols[0]['fields'].push({
      'name': 'building',
      'type': {
        'type': 'enum',
        'name': 'Building'
      }
    })
    const component = mountWithIntl(<EntityTypeViewer schema={JSON.stringify(entityTypeWithoutSymbols)} />)
    // TODO: Updates when styles are added to rendered components
    expect(component.html()).toContain('<span class="type"> enum</span>')
    expect(component.html()).toContain('<span class="name">building</span>')
  })

  it('should take schema JSON with a min depth of 3', () => {
    const entityTypeDepth3 = [...mockEntityTypesSchema]
    entityTypeDepth3[1]['fields'][2]['type']['fields'].push({name: 'cordinates',
      type: {type: 'record', name: 'coordinates', fields: [{name: 'Y', type: 'string'}, {name: 'X', type: 'int'}]}})
    const component = mountWithIntl(<EntityTypeViewer schema={JSON.stringify(entityTypeDepth3)} />)
    expect(component.html()).toContain('location.cordinates.Y')
  })
})
