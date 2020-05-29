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

import React from 'react'
import { FormattedMessage, defineMessages, useIntl } from 'react-intl'

import { clone, isEmpty, generateGUID } from '../utils'
import { parseSchema, isOptionalType, isPrimitive, typeToString } from '../utils/avro-utils'
import { AVRO_EXTENDED_TYPE, MASKING_ANNOTATION, MASKING_PUBLIC } from '../utils/constants'

const MESSAGES = defineMessages({
  nullable: {
    defaultMessage: '(nullable)',
    id: 'avro.schema.nullable'
  }
})

const getPath = (parent, field) => `${parent ? parent + '.' : ''}${field.name || '#'}`

const isMasked = (field) => (
  Boolean(
    field &&
    field[MASKING_ANNOTATION] &&
    field[MASKING_ANNOTATION].toLowerCase() !== MASKING_PUBLIC
  )
)

const getHighlightedClassName = (path, highlight, className) => {
  // the simplest way (equality)
  // TODO: check that the jsonPath is included in any of the keys,
  // because they can also be "formulas"
  const keys = Object.keys(highlight || {})
  for (let i = 0; i < keys.length; i++) {
    if (keys[i] === path) {
      return `${className}-mapped-${highlight[keys[i]]}`
    }
  }

  return ''
}

const AvroSchemaViewer = ({ className, hideChildren, highlight, pathPrefix, schema }) => {
  const { formatMessage } = useIntl()
  if (isEmpty(schema)) {
    return (
      <div className='hint'>
        <FormattedMessage
          id='avro.schema.empty'
          defaultMessage='Your AVRO schema will be displayed here once you have added a valid source.'
        />
      </div>
    )
  }

  const renderField = (field, parentJsonPath = null) => {
    const nullableStr = formatMessage(MESSAGES.nullable)

    const jsonPath = getPath(parentJsonPath, field)
    const highlightedClassName = getHighlightedClassName(jsonPath, highlight, className)
    const type = typeToString(field.type, nullableStr, !hideChildren, field[AVRO_EXTENDED_TYPE])

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
    if (!hideChildren) {
      if (currentType.type === 'record') {
        children = currentType.fields.map(f => renderField(f, jsonPath))
      }
      if (currentType.type === 'array' && !isPrimitive(currentType.items)) {
        children = renderField({ type: currentType.items }, jsonPath)
      }
      if (currentType.type === 'map' && !isPrimitive(currentType.values)) {
        children = renderField({ type: currentType.values }, jsonPath)
      }
      if (isUnion) { // union type
        children = currentType.map((t, i) => renderField({ name: `${i + 1}`, type: t }, jsonPath))
      }

      if (children) {
        children = (
          <div
            data-test={jsonPath + '.$'}
            key={generateGUID()}
            className={(isUnion ? 'group-union' : 'group-list')}
          >
            {children}
          </div>
        )
      }
    }

    return (
      <div data-test={jsonPath} key={generateGUID()} className='group'>
        {
          field.name &&
            <div className={highlightedClassName + (children ? ' group-title' : ' field')}>
              {isMasked(field) && <i className='fas fa-lock' />}
              <span className='name'>{field.name}</span>
              <span className='type'>{type}</span>
            </div>
        }
        {children}
      </div>
    )
  }

  try {
    parseSchema(schema)

    if (schema.type !== 'record') {
      return (
        <div className='hint error-message'>
          <FormattedMessage
            id='avro.schema.type.not.record'
            defaultMessage='Initial AVRO schema type can only be of type "record".'
          />
        </div>
      )
    }

    return (
      <div className={className}>
        <div className='group'>
          <div data-test={`group-title-${schema.name}`} className='title group-title'>
            {schema.name}
          </div>
          <div className='properties group-list'>
            {schema.fields.map(f => renderField(clone(f), pathPrefix))}
          </div>
        </div>
      </div>
    )
  } catch (error) {
    return (
      <div className='hint'>
        <FormattedMessage
          id='avro.schema.invalid'
          defaultMessage='You have provided an invalid AVRO schema.'
        />
      </div>
    )
  }
}

export default AvroSchemaViewer
