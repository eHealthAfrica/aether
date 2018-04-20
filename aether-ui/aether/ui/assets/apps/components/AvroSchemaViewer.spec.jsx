/* global describe, it, expect */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import mockAvroSchema from '../mock/schema_input.mock'
import { AvroSchemaViewer } from '../components'

describe('AvroSchemaViewer', () => {
  it('should take a valid avro schema and render an avro visualizer', () => {
    const component = mountWithIntl(<AvroSchemaViewer schema={mockAvroSchema} />)
    expect(component.find('[data-qa^="group-title-"]').length).toEqual(9)
    expect(component.find('[data-qa="no-children-surname"]').html()).toContain('<span class="name">surname</span>')
  })

  it('should take a invalid avro schema and render an invalid error message', () => {
    delete mockAvroSchema['name']
    const component = mountWithIntl(<AvroSchemaViewer schema={mockAvroSchema} />)
    expect(component.html()).toContain('You have provided an invalid AVRO schema.')
  })

  it('should render an empty avro schema viewer', () => {
    const component = mountWithIntl(<AvroSchemaViewer />)
    expect(component.html()).toContain('Your schema for this pipeline will be displayed here once you have added an AVRO schema.')
  })
})
