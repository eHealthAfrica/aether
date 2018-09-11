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

/* global describe, it, expect */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import mockEntityTypesSchema from '../../tests/mock/schema_entityTypes.mock.json'
import { EntityTypeViewer } from '../components'

describe('EntityTypeViewer', () => {
  it('should take a valid json list of schemas and render entity visualizers', () => {
    const component = mountWithIntl(<EntityTypeViewer schema={mockEntityTypesSchema}
      highlight={['Person.firstName']} />)
    expect(component.find('div.entity-types-schema').children().length).toEqual(2)
    expect(component.html()).not.toContain('Invalid entity type')
    expect(component.html()).not.toContain('Invalid schema')
    expect(component.find('[id="entityType_Person.lastName"]').html())
      .toContain('<span class="type"> (nullable)</span>')
    expect(component.find('[id="entityType_Person.age"]').html())
      .toContain('<span class="type"> int,string</span>')
    expect(component.find('[id="entityType_Person.age"]').html())
      .toContain('<i class="fas fa-lock"></i>')
    expect(component.find('[id="entityType_Person.lastName"]').html())
      .not.toContain('<i class="fas fa-lock"></i>')
  })

  it('should take a valid json with empty entities', () => {
    const validJSONWithEmptyObjects = [{}, {}, {}]
    const component = mountWithIntl(<EntityTypeViewer schema={validJSONWithEmptyObjects} />)
    expect(component.find('div.entity-types-schema').children().length).toEqual(3)
    expect(component.html()).toContain('Invalid entity type')
  })

  it('should take an empty schema and render error', () => {
    const inValidSchema = []
    const component = mountWithIntl(<EntityTypeViewer schema={inValidSchema} />)
    expect(component.html()).toContain('No Entity Types added to this pipeline yet.')
  })

  it('should take an empty schema input and render message', () => {
    const component = mountWithIntl(<EntityTypeViewer />)
    expect(component.html()).toContain('No entity types added to this pipeline yet.')
  })

  it('should take entity type without fields', () => {
    const entityTypeWithoutProperties = [{ name: 'test-name', type: 'record', fields: [] }]
    const component = mountWithIntl(<EntityTypeViewer schema={entityTypeWithoutProperties} />)
    expect(component.html()).toContain('Entity has no properties')
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
    const component = mountWithIntl(
      <EntityTypeViewer schema={entityTypeWithoutSymbols} highlight={['Person.firstName']} />
    )
    expect(component.html()).toContain('<span class="type"> enum</span>')
    expect(component.html()).toContain('<span class="name">building</span>')
  })

  it('should take schema JSON with a min depth of 3', () => {
    const entityTypeDepth3 = [...mockEntityTypesSchema]
    entityTypeDepth3[1]['fields'][2]['type']['fields'].push({
      name: 'cordinates',
      type: {
        type: 'record',
        name: 'coordinates',
        fields: [
          { name: 'Y', type: 'string' },
          { name: 'X', type: 'int' }
        ]
      }
    })
    const component = mountWithIntl(
      <EntityTypeViewer schema={entityTypeDepth3} highlight={['Person.firstName']} />
    )
    expect(component.html()).toContain('location.cordinates.Y')
  })
})
