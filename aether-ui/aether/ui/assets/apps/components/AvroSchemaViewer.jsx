import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import avro from 'avsc'

import {clone} from '../utils'

class AvroSchemaViewer extends Component {
  getHighlightedClassName (jsonPath) {
    const {highlight} = this.props
    // the simplest way (equality)
    // TODO: check that the jsonPath is included in any of the keys,
    // because they can also be "formulas"
    const keys = Object.keys(highlight)
    for (let i = 0; i < keys.length; i++) {
      if (keys[i] === jsonPath) {
        return `input-mapped-${highlight[keys[i]]}`
      }
    }

    return ''
  }

  // parent is passed if schema fields in view are nested.
  schemaToMarkup (schema, parent = null) {
    if (schema.fields && schema.fields.length) {
      const jsonPath = `${parent || schema.name}`
      const className = this.getHighlightedClassName(jsonPath)

      return (
        <ul key={schema.name} className='group'>
          <li
            data-qa={`group-title-${schema.name}`}
            className={`group-title ${className}`}
            id={`input_${jsonPath}`}>
            {schema.name}
          </li>
          <li>
            <ul key={schema.name} className='group-list'>
              { schema.fields.map(field => this.schemaToMarkup(field, parent)) }
            </ul>
          </li>
        </ul>
      )
    } else if (typeof schema.type !== 'string') {
      schema.type.name = schema.name
      return (
        this.schemaToMarkup(schema.type, `${parent ? parent + '.' : ''}${schema.name}`)
      )
    } else {
      const jsonPath = `${parent ? parent + '.' : ''}${schema.name}`
      const className = this.getHighlightedClassName(jsonPath)

      return (
        <li
          data-qa={`no-children-${schema.name}`}
          key={schema.name}
          className={className}
          id={`input_${jsonPath}`}>
          <span className='name'>{schema.name}</span>
          <span className='type'> {schema.type}</span>
        </li>
      )
    }
  }

  render () {
    if (!this.props.schema || !Object.keys(this.props.schema).length) {
      return (
        <div className='hint'>
          <FormattedMessage
            id='pipeline.input.empty.message'
            defaultMessage='Your schema for this pipeline will be displayed here once you have added a valid source.'
          />
        </div>
      )
    }

    try {
      avro.parse(this.props.schema, { noAnonymousTypes: true })
      return (
        <div className='input-schema'>
          { this.schemaToMarkup(clone(this.props.schema)) }
        </div>
      )
    } catch (error) {
      return (
        <div className='hint'>
          <FormattedMessage
            id='pipeline.input.invalid.message'
            defaultMessage='You have provided an invalid AVRO schema.'
          />
        </div>
      )
    }
  }
}

export default AvroSchemaViewer
