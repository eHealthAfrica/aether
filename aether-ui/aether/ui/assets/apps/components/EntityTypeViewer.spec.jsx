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

/* global describe, it, expect */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import { mockEntityTypes } from '../../tests/mock'
import { EntityTypeViewer } from '../components'

describe('EntityTypeViewer', () => {
  it('should take an empty schema and render error', () => {
    const component = mountWithIntl(<EntityTypeViewer schema={[]} />)
    expect(component.text()).toContain('No entity types added yet.')
  })

  it('should take an empty schema input and render message', () => {
    const component = mountWithIntl(<EntityTypeViewer />)
    expect(component.text()).toContain('No entity types added yet.')
  })

  it('should take a valid json with empty entities and render error', () => {
    const component = mountWithIntl(<EntityTypeViewer schema={[{}, {}, {}]} />)
    expect(component.find('div.entity-types-schema').children().length).toEqual(3)
    expect(component.text()).toContain('Invalid entity type')
  })

  it('should not take entity type that is not a record', () => {
    const entities = [{ name: 'test-name', type: 'string' }]
    const component = mountWithIntl(<EntityTypeViewer schema={entities} />)
    expect(component.text()).toContain('Entity type can only be of type "record"')
  })

  it('should not take entity type of type record without fields', () => {
    const entities = [{ name: 'test-name', type: 'record', fields: [] }]
    const component = mountWithIntl(<EntityTypeViewer schema={entities} />)
    expect(component.text()).toContain('Invalid entity type')
  })

  it('should not render enum type if symbols are missing', () => {
    const entities = [{
      name: 'test-name',
      type: 'record',
      fields: [
        {
          name: 'building',
          type: {
            type: 'enum',
            name: 'Building'
          }
        }
      ]
    }]

    const component = mountWithIntl(<EntityTypeViewer schema={entities} />)
    expect(component.text()).toContain('Invalid entity type')
  })

  it('should take a valid json list of schemas and render entity visualizers', () => {
    const highlight = [
      'Person.firstName',
      'Screening.id'
    ]
    const component = mountWithIntl(
      <EntityTypeViewer schema={mockEntityTypes} highlight={highlight} />
    )

    expect(component.text()).not.toContain('Invalid entity type')
    expect(component.text()).not.toContain('Invalid schema')

    expect(component.find('div.entity-types-schema').children().length).toEqual(2)

    expect(component.find('[data-qa="Person.firstName"]').html())
      .toContain('<li data-qa="Person.firstName" class="entityType-mapped">')

    expect(component.find('[data-qa="Person.lastName"]').html())
      .toContain('<span class="type">string (nullable)</span>')
    expect(component.find('[data-qa="Person.lastName"]').html())
      .not.toContain('<i class="fas fa-lock"></i>')

    expect(component.find('[data-qa="Person.age"]').html())
      .toContain('<span class="type">union: int, string</span>')
    expect(component.find('[data-qa="Person.age"]').html())
      .toContain('<i class="fas fa-lock"></i>')

    expect(component.find('[data-qa="Screening.id"]').html())
      .toContain('<li data-qa="Screening.id" class="entityType-mapped">')
    expect(component.find('[data-qa="Screening.location"]').html())
      .toContain('<span class="type">record</span>')
  })
})
