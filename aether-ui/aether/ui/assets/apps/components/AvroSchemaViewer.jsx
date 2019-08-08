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

import React, { Component } from 'react'
import { FormattedMessage, defineMessages, injectIntl } from 'react-intl'

import { clone, isEmpty, generateGUID } from '../utils'
import { parseSchema, isOptionalType, isPrimitive, typeToString } from '../utils/avro-utils'

const MESSAGES = defineMessages({
  nullable: {
    defaultMessage: '(nullable)',
    id: 'avro.schema.nullable'
  }
})

const getPath = (parent, field) => `${parent ? parent + '.' : ''}${field.name || '#'}`

class AvroSchemaViewer extends Component {
  render () {
    if (isEmpty(this.props.schema)) {
      return (
        <div className='hint'>
          <FormattedMessage
            id='schema.empty'
            defaultMessage='Your AVRO schema will be displayed here once you have added a valid source.'
          />
        </div>
      )
    }

    try {
      parseSchema(this.props.schema)

      return (
        <div className='input-schema'>
          <div className='group'>
            <div
              data-qa={`group-title-${this.props.schema.name}`}
              className={`group-title ${this.props.className || ''}`}
            >
              { this.props.schema.name }
            </div>
            <div className='group-list'>
              { this.props.schema.fields.map(f => this.renderField(clone(f))) }
            </div>
          </div>
        </div>
      )
    } catch (error) {
      return (
        <div className='hint'>
          <FormattedMessage
            id='schema.invalid'
            defaultMessage='You have provided an invalid AVRO schema.'
          />
        </div>
      )
    }
  }

  renderField (field, parentJsonPath = null) {
    const { formatMessage } = this.props.intl
    const nullableStr = formatMessage(MESSAGES.nullable)

    const jsonPath = getPath(parentJsonPath, field)
    const highlightedClassName = this.getHighlightedClassName(jsonPath)
    const type = typeToString(field.type, nullableStr, true)

    let currentType = (field.type.type || field.type) && field.type
    if (isOptionalType(currentType)) {
      // remove "null" item
      currentType = currentType.filter(typeItem => typeItem !== 'null')
    }
    if (Array.isArray(currentType) && currentType.length === 1) {
      // this is a fake union type, extract the real type
      currentType = currentType[0]
      currentType = (currentType.type || currentType) && currentType
    }

    const isUnion = Array.isArray(currentType) && !isPrimitive(currentType)

    let children = null
    if (currentType.type === 'record') {
      children = currentType.fields.map(f => this.renderField(f, jsonPath))
    }
    if (currentType.type === 'array' && !isPrimitive(currentType.items)) {
      children = this.renderField({ type: currentType.items }, jsonPath)
    }
    if (currentType.type === 'map' && !isPrimitive(currentType.values)) {
      children = this.renderField({ type: currentType.values }, jsonPath)
    }
    if (isUnion) { // union type
      children = currentType.map((t, i) => this.renderField({ name: `${i + 1}`, type: t }, jsonPath))
    }

    if (children) {
      children = (
        <div
          data-qa={jsonPath + '.$'}
          key={generateGUID()}
          className={(isUnion ? 'group-union' : 'group-list')}
        >
          { children }
        </div>
      )
    }

    return (
      <div data-qa={jsonPath} key={generateGUID()} className='group'>
        { field.name &&
          <div className={highlightedClassName + (children ? ' group-title' : ' field')}>
            <span className='name'>{ field.name }</span>
            <span className='type'>{ type }</span>
          </div>
        }
        { children }
      </div>
    )
  }

  getHighlightedClassName (jsonPath) {
    const { highlight } = this.props
    // the simplest way (equality)
    // TODO: check that the jsonPath is included in any of the keys,
    // because they can also be "formulas"
    const keys = Object.keys(highlight || {})
    for (let i = 0; i < keys.length; i++) {
      if (keys[i] === jsonPath) {
        return `input-mapped-${highlight[keys[i]]}`
      }
    }

    return ''
  }
}

export default injectIntl(AvroSchemaViewer)
