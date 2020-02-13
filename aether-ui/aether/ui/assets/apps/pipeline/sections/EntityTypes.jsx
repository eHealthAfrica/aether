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

import React, { useState, useEffect } from 'react'
import { FormattedMessage, defineMessages, useIntl } from 'react-intl'
import { connect } from 'react-redux'

import { AvroSchemaViewer } from '../../components'
import { deepEqual, objectToString } from '../../utils'
import { FIELD_ID, parseSchema } from '../../utils/avro-utils'
import { updateContract } from '../redux'

const MESSAGES = defineMessages({
  nonObjectError: {
    defaultMessage: 'The AVRO schema can only be of type "record".',
    id: 'entity.types.error.non-object'
  },
  missingIdError: {
    defaultMessage: 'The AVRO schema MUST have an "id" field with type "string".',
    id: 'entity.types.missing-id-field'
  },
  uniqueNamesError: {
    defaultMessage: 'The schema names cannot be repeated.',
    id: 'entity.types.error.repeatedNames'
  },
  entityTypeSchemaPlaceHolder: {
    defaultMessage: 'Enter your schemas',
    id: 'entity.types.schema.placeholder'
  },
  schema: {
    defaultMessage: 'Schema',
    id: 'entity.type.schema'
  }
})

const EntityTypes = ({ contract, updateContract }) => {
  const { formatMessage } = useIntl()

  const [prevContract, setPrevContract] = useState(contract)
  const [entityTypesSchema, setEntityTypesSchema] = useState(objectToString(contract.entity_types))
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!deepEqual(prevContract.entity_types, contract.entity_types)) {
      setPrevContract(contract)
      setError(null)
      setEntityTypesSchema(objectToString(contract.entity_types))
    }
  })

  const notifyChange = (event) => {
    event.preventDefault()
    event.stopPropagation()

    if (contract.is_read_only) {
      return
    }

    try {
      // validate schemas
      const schemas = JSON.parse(entityTypesSchema)
      schemas.forEach((schema, index) => {
        const current = `${formatMessage(MESSAGES.schema)} ${index + 1}`
        try {
          parseSchema(schema)
        } catch (error) {
          throw new Error(`${current}: ${error.message}`)
        }

        if (schema.type !== 'record') {
          throw new Error(`${current}: ${formatMessage(MESSAGES.nonObjectError)}`)
        }

        // all entity types must have an "id" field with type "string"
        if (!schema.fields.find(field => field.name === FIELD_ID && field.type === 'string')) {
          throw new Error(`${current}: ${formatMessage(MESSAGES.missingIdError)}`)
        }
      })

      const names = new Set(schemas.map(({ name }) => name))
      if (names.size !== schemas.length) {
        throw new Error(formatMessage(MESSAGES.uniqueNamesError))
      }

      updateContract({ ...contract, entity_types: schemas, is_identity: false })
    } catch (error) {
      setError(error.message)
    }
  }

  const hasChanged = () => {
    try {
      const schemas = JSON.parse(entityTypesSchema)
      return !deepEqual(schemas, contract.entity_types)
    } catch (e) {
      return true
    }
  }

  return (
    <div className='section-body'>
      <div className='section-left'>
        {
          (contract.entity_types || []).map((entityType, index) => (
            <AvroSchemaViewer
              key={index}
              schema={entityType}
              highlight={contract.highlightDestination}
              pathPrefix={entityType.name}
              className='entity-type'
              hideChildren
            />
          ))
        }
      </div>

      <div className='section-right'>
        <form onSubmit={notifyChange}>
          <label className='form-label'>
            <FormattedMessage
              id='entity.types.empty'
              defaultMessage='Paste Entity Type definitions'
            />
          </label>

          <div className='textarea-header'>
            {
              error &&
                <div className='hint error-message'>
                  <h4 className='hint-title'>
                    <FormattedMessage
                      id='entity.types.invalid'
                      defaultMessage='You have provided invalid AVRO schemas.'
                    />
                  </h4>
                  {error}
                </div>
            }
          </div>

          <textarea
            className={`input-d monospace ${error ? 'error' : ''}`}
            value={entityTypesSchema}
            onChange={(event) => { setEntityTypesSchema(event.target.value) }}
            placeholder={formatMessage(MESSAGES.entityTypeSchemaPlaceHolder)}
            rows='10'
            disabled={contract.is_read_only}
          />

          {
            !contract.is_read_only &&
              <button
                type='submit'
                className='btn btn-d btn-primary mt-3'
                disabled={!hasChanged()}
              >
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

const mapStateToProps = ({ pipelines }) => ({
  contract: pipelines.currentContract
})
const mapDispatchToProps = { updateContract }

export default connect(mapStateToProps, mapDispatchToProps)(EntityTypes)
