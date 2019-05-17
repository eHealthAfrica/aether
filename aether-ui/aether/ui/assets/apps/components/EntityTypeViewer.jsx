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
import { FormattedMessage } from 'react-intl'

import { generateGUID } from '../utils'
import { MASKING_ANNOTATION, MASKING_PUBLIC } from '../utils/constants'

const PropertyList = (props) => {
  const isMasked = (field) => (
    Boolean(
      field &&
      field[MASKING_ANNOTATION] &&
      field[MASKING_ANNOTATION].toLowerCase() !== MASKING_PUBLIC
    )
  )

  if (!props.fields || !props.fields.length) {
    return (
      <FormattedMessage
        id='viewer.entity.type.no-fields'
        defaultMessage='Entity has no properties'
      />
    )
  }

  return props.fields.map(field => {
    if (field.type.fields) {
      let parent = null
      if (props.parent) {
        parent = `${props.parent}.${field.name}`
      } else {
        parent = field.name
      }

      return PropertyList({
        highlight: props.highlight,
        fields: field.type.fields,
        parent,
        name: props.name
      })
    } else if (Array.isArray(field.type)) {
      let typeStringOptions = null
      let isNullable = false

      field.type.forEach(typeItem => {
        if (!typeStringOptions) {
          typeStringOptions = []
        }
        if (typeof typeItem === 'string') {
          if (typeItem === 'null') {
            isNullable = true
          } else {
            typeStringOptions.push(typeItem)
          }
        } else if (typeof typeItem === 'object') {
          typeStringOptions.push(typeItem.type)
        }
      })

      return PropertyList({
        highlight: props.highlight,
        fields: [{
          ...field,
          name: field.name,
          type: typeStringOptions.toString()
        }],
        name: props.name,
        parent: props.parent,
        isNullable
      })
    } else {
      let fieldType = ''

      if (typeof field.type === 'object') {
        fieldType = field.type.symbols ? `{${field.type.symbols.toString()}}` : field.type.type
      } else {
        fieldType = field.type
      }

      if (props.parent) {
        const jsonPath = `${props.name}.${props.parent}.${field.name}`
        const className = props.highlight.indexOf(jsonPath) > -1 ? 'entityType-mapped' : ''

        return (
          <li
            key={`${props.parent}.${field.name}`}
            className={className}
            id={`entityType_${jsonPath}`}
          >
            { isMasked(field) && <i className='fas fa-lock' /> }
            <span className='name'>
              { `${props.parent}.${field.name}` }
            </span>
            <span className='type'>
              { fieldType === 'enum' && field.symbols
                ? `${fieldType}: [${field.symbols.toString()}]`
                : fieldType
              }
            </span>
            { props.isNullable && <span className='type'> (nullable)</span> }
          </li>
        )
      } else {
        const jsonPath = `${props.name}.${field.name}`
        const className = props.highlight.indexOf(jsonPath) > -1 ? 'entityType-mapped' : ''

        return (
          <li
            key={field.name}
            className={className}
            id={`entityType_${jsonPath}`}
          >
            { isMasked(field) && <i className='fas fa-lock' /> }
            <span className='name'>{ field.name }</span>
            <span className='type'> { fieldType }</span>
            { props.isNullable && <span className='type'> (nullable)</span> }
          </li>
        )
      }
    }
  })
}

const EntityType = props => {
  return (
    <div className='entity-type'>
      <h2 className='title'>{ props.name }</h2>
      <ul className='properties'>
        <PropertyList
          highlight={props.highlight}
          fields={props.fields}
          name={props.name}
        />
      </ul>
    </div>
  )
}

class EntityTypeViewer extends Component {
  iterateList (list) {
    return list.map(entityType => {
      if (entityType.name && entityType.fields) {
        return (
          <EntityType
            key={entityType.name}
            highlight={this.props.highlight}
            name={entityType.name}
            fields={entityType.fields}
          />
        )
      } else {
        return (
          <div className='hint' key={generateGUID()}>
            <FormattedMessage
              id='viewer.entity.type.invalid'
              defaultMessage='Invalid entity type'
            />
          </div>
        )
      }
    })
  }

  render () {
    if (!this.props.schema || !this.props.schema.length) {
      return (
        <div className='hint'>
          <FormattedMessage
            id='viewer.entity.types.empty'
            defaultMessage='No entity types added to this pipeline yet.'
          />
        </div>
      )
    }

    return (
      <div className='entity-types-schema'>
        { this.iterateList(this.props.schema) }
      </div>
    )
  }
}

export default EntityTypeViewer
