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

import { MASKING_ANNOTATION, MASKING_PUBLIC } from '../utils/constants'
import { parseSchema, typeToString } from '../utils/avro-utils'

const MESSAGES = defineMessages({
  nullable: {
    defaultMessage: '(nullable)',
    id: 'entity.types.nullable'
  }
})

const isMasked = (field) => (
  Boolean(
    field &&
    field[MASKING_ANNOTATION] &&
    field[MASKING_ANNOTATION].toLowerCase() !== MASKING_PUBLIC
  )
)

class EntityTypeViewer extends Component {
  render () {
    if (!this.props.schema || this.props.schema.length === 0) {
      return (
        <div className='hint'>
          <FormattedMessage
            id='viewer.entity.types.empty'
            defaultMessage='No entity types added yet.'
          />
        </div>
      )
    }

    return (
      <div className='entity-types-schema'>
        { this.props.schema.map(this.renderEntityType.bind(this)) }
      </div>
    )
  }

  renderEntityType (entityType, index) {
    const { formatMessage } = this.props.intl
    const nullable = formatMessage(MESSAGES.nullable)
    const highlight = this.props.highlight || []

    try {
      parseSchema(entityType)

      if (entityType.type !== 'record') {
        return (
          <div key={index} className='hint error-message'>
            <FormattedMessage
              id='viewer.entity.type.not.record'
              defaultMessage='Entity type can only be of type "record"'
            />
          </div>
        )
      }

      return (
        <div key={entityType.name} className='entity-type'>
          <h2 className='title'>{ entityType.name }</h2>
          <ul className='properties'>
            {
              entityType.fields.map(field => {
                const jsonPath = `${entityType.name}.${field.name}`
                return (
                  <li
                    key={field.name}
                    data-qa={jsonPath}
                    className={highlight.indexOf(jsonPath) > -1 ? 'entityType-mapped' : ''}
                  >
                    { isMasked(field) && <i className='fas fa-lock' /> }
                    <span className='name'>{ field.name }</span>
                    <span className='type'>{ typeToString(field.type, nullable) }</span>
                  </li>
                )
              })
            }
          </ul>
        </div>
      )
    } catch (error) {
      return (
        <div key={index} className='hint error-message'>
          <FormattedMessage
            id='viewer.entity.type.invalid'
            defaultMessage='Invalid entity type'
          />
          <p>
            { error.toString() }
          </p>
        </div>
      )
    }
  }
}

export default injectIntl(EntityTypeViewer)
