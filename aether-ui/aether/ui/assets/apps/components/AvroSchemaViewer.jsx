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
  schemaToMarkup (schema, parent = null, isUnion = false, isItem = false) {
    if (schema.fields && schema.fields.length) {
      const jsonPath = `${parent || schema.name}`
      const className = this.getHighlightedClassName(jsonPath)

      return isUnion ? (
        <ul key={schema.name} className='group-list'>
          { schema.fields.map(field => this.schemaToMarkup(field, parent, isUnion, isItem)) }
        </ul>
      ) : (
        <ul key={schema.name} className='group'>
          <li
            data-qa={`group-title-${schema.name}`}
            className={`group-title ${className}`}
            id={`input_${jsonPath}`}>
            {schema.name}
          </li>
          <li>
            <ul key={schema.name} className='group-list'>
              { schema.fields.map(field => this.schemaToMarkup(field, parent, isUnion, isItem)) }
            </ul>
          </li>
        </ul>
      )
    } else if (Array.isArray(schema.type)) {
      let typeStringOptions = []
      const typeObjectOptions = []
      let isNullable = false
      schema.type.forEach(typeItem => {
        if (typeof typeItem === 'string') {
          if (typeItem === 'null') {
            isNullable = true
          } else {
            typeStringOptions.push(typeItem)
          }
        } else if (typeof typeItem === 'object') {
          typeStringOptions.push(typeof typeItem.type === 'string' ? typeItem.type : typeof typeItem.type)
          typeObjectOptions.push(typeItem)
        }
      })
      const nestedList = typeObjectOptions.length && typeObjectOptions.map(obj => (this.schemaToMarkup(obj,
        `${parent ? parent + '.' : ''}${schema.name}`, true, isItem)))
      return this.deepestRender(schema, parent, true, isItem, typeStringOptions, isNullable, nestedList !== 0 && <ul>{nestedList}</ul>)
    } else if (typeof schema.type !== 'string') {
      schema.type.name = schema.name
      let parentName = ''
      if (parent) {
        parentName = schema.type.type === 'array' ? parent : `${parent}.${schema.name}`
      } else {
        parentName = schema.name
      }
      return this.schemaToMarkup(schema.type, parentName, isUnion, isItem)
    } else {
      return this.deepestRender(schema, parent, isUnion, isItem)
    }
  }

  deepestRender (schema, parent = null, isUnion = false, isItem = false, typesOptions = null, isNullable = false, children = null) {
    const jsonPath = `${parent ? parent + '.' : ''}${schema.name}`
    const className = this.getHighlightedClassName(jsonPath)
    let arrayItems = null
    if (schema.type === 'array' && typeof schema.items !== 'string') {
      arrayItems = this.schemaToMarkup(schema.items, parent, isUnion, true)
    }
    return (
      <li
        data-qa={`no-children-${schema.name}`}
        key={schema.name}
        className={className}
        id={`input_${jsonPath}`}>
        {schema.name && (<span>
          <span className={isItem ? 'name item' : 'name'}>{schema.name}</span>
          <span className='type'> {typesOptions && typesOptions.length ? typesOptions.toString() : schema.type}</span></span>)
        }
        { isNullable && <span className='type'> (nullable)</span> }
        { arrayItems }
        { children }
      </li>
    )
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
