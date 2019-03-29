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

import React, { Component } from 'react'
import { FormattedMessage, defineMessages, injectIntl } from 'react-intl'
import { connect } from 'react-redux'

import { EntityTypeViewer } from '../../components'
import { deepEqual, objectToString } from '../../utils'
import { parseSchema } from '../../utils/avro-utils'
import { updateContract } from '../redux'

const MESSAGES = defineMessages({
  missingIdError: {
    defaultMessage: 'The AVRO schemas MUST have an "id" field with type "string".',
    id: 'entity.types.missing-id-field'
  },
  entityTypeSchemaPlaceHolder: {
    defaultMessage: 'Enter your schemas',
    id: 'entity.types.schema.placeholder'
  }
})

class EntityTypes extends Component {
  constructor (props) {
    super(props)

    this.state = {
      entityTypesSchema: objectToString(props.contract.entity_types),
      error: null
    }
  }

  componentDidUpdate (prevProps) {
    if (!deepEqual(prevProps.contract.entity_types, this.props.contract.entity_types)) {
      this.setState({
        entityTypesSchema: objectToString(this.props.contract.entity_types),
        error: null
      })
    }
  }

  onSchemaTextChanged (event) {
    this.setState({
      entityTypesSchema: event.target.value
    })
  }

  notifyChange (event) {
    event.preventDefault()
    if (this.props.contract.is_read_only) {
      return
    }

    const { formatMessage } = this.props.intl

    try {
      // validate schemas
      const schemas = JSON.parse(this.state.entityTypesSchema)
      schemas.forEach(schema => {
        parseSchema(schema)
        // all entity types must have an "id" field with type "string"
        if (!schema.fields.find(field => field.name === 'id' && field.type === 'string')) {
          throw new Error(formatMessage(MESSAGES.missingIdError))
        }
      })
      this.props.updateContract({ ...this.props.contract, entity_types: schemas })
    } catch (error) {
      this.setState({ error: error.message })
    }
  }

  hasChanged () {
    try {
      const schemas = JSON.parse(this.state.entityTypesSchema)
      return !deepEqual(schemas, this.props.contract.entity_types)
    } catch (e) {
      return true
    }
  }

  render () {
    const { formatMessage } = this.props.intl

    return (
      <div className='section-body'>
        <div className='section-left'>
          <EntityTypeViewer
            schema={this.props.contract.entity_types}
            highlight={this.props.contract.highlightDestination}
          />
        </div>

        <div className='section-right'>
          <form onSubmit={this.notifyChange.bind(this)}>
            <label className='form-label'>
              <FormattedMessage
                id='entity.types.empty'
                defaultMessage='Paste Entity Type definitions'
              />
            </label>

            <div className='textarea-header'>
              { this.state.error &&
                <div className='hint error-message'>
                  <h4 className='hint-title'>
                    <FormattedMessage
                      id='entity.types.invalid'
                      defaultMessage='You have provided invalid AVRO schemas.'
                    />
                  </h4>
                  { this.state.error }
                </div>
              }
            </div>

            <textarea
              className={`input-d monospace ${this.state.error ? 'error' : ''}`}
              value={this.state.entityTypesSchema}
              onChange={this.onSchemaTextChanged.bind(this)}
              placeholder={formatMessage(MESSAGES.entityTypeSchemaPlaceHolder)}
              rows='10'
              disabled={this.props.contract.is_read_only}
            />

            { !this.props.contract.is_read_only &&
              <button type='submit' className='btn btn-d btn-primary mt-3' disabled={!this.hasChanged()}>
                <span className='details-title'>
                  <FormattedMessage
                    id='entity.types.button.ok'
                    defaultMessage='Add to pipeline'
                  />
                </span>
              </button>
            }
          </form>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  contract: pipelines.currentContract
})
const mapDispatchToProps = { updateContract }

export default connect(mapStateToProps, mapDispatchToProps)(injectIntl(EntityTypes))
