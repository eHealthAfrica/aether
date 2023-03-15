/*
 * Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import { AvroSchemaViewer, ViewsBar } from '../../components'
import { deepEqual, objectToString } from '../../utils'
import { generateSchema, randomInput } from '../../utils/avro-utils'

import { updatePipeline } from '../redux'

const SCHEMA_VIEW = 'SCHEMA_VIEW'
const DATA_VIEW = 'DATA_VIEW'

const MESSAGES = defineMessages({
  avroSchemaView: {
    defaultMessage: 'Avro Schema',
    id: 'input.schema.view'
  },
  avroSchemaPlaceholder: {
    defaultMessage: 'Paste an AVRO Schema and Sample Data will be generated for your convenience to use in the pipeline.',
    id: 'input.schema.placeholder'
  },
  avroSchemaSubmitButton: {
    defaultMessage: 'Add to pipeline',
    id: 'input.schema.submit'
  },
  avroSchemaInvalidError: {
    defaultMessage: 'You have provided an invalid AVRO schema.',
    id: 'input.schema.error.invalid'
  },
  avroSchemaGenericError: {
    defaultMessage: 'Input data could not be generated from the schema provided.',
    id: 'input.schema.error.invalid.generic'
  },
  avroSchemaNonObjectError: {
    defaultMessage: 'The AVRO schema can only be of type "record".',
    id: 'input.schema.error.non-object'
  },

  inputDataView: {
    defaultMessage: 'JSON Data',
    id: 'input.data.view'
  },
  inputDataPlaceholder: {
    defaultMessage: 'Once you have added a schema, we will generate some sample data for you. Alternatively, you can enter some JSON data and Aether will derive an AVRO schema for you.',
    id: 'input.data.placeholder'
  },
  inputDataSubmitButton: {
    defaultMessage: 'Derive schema from data',
    id: 'input.data.submit'
  },

  jsonInvalidError: {
    defaultMessage: 'Not a valid JSON document.',
    id: 'input.json.error.invalid'
  },
  jsonNonObjectError: {
    defaultMessage: 'The JSON document can only be a valid dictionary.',
    id: 'input.json.error.non-object'
  }
})

const Input = ({ pipeline, highlight, updatePipeline }) => {
  const { formatMessage } = useIntl()
  const [view, setView] = useState(DATA_VIEW)
  const [prevPipeline, setPrevPipeline] = useState(pipeline)

  const [schemaStr, setSchemaStr] = useState(objectToString(pipeline.schema))
  const [schemaErr, setSchemaErr] = useState(null)

  const [inputStr, setInputStr] = useState(objectToString(pipeline.input))
  const [inputErr, setInputErr] = useState(null)

  useEffect(() => {
    if (!deepEqual(prevPipeline, pipeline)) {
      setPrevPipeline(pipeline)
      setSchemaStr(objectToString(pipeline.schema))
      setSchemaErr(null)
      setInputStr(objectToString(pipeline.input))
      setInputErr(null)
    }
  })

  const parseJson = () => {
    try {
      const obj = JSON.parse(currentValue)

      // the JSON cannot be an array or a primitive, only an object
      if (Object.prototype.toString.call(obj) !== '[object Object]') {
        setError({
          message: formatMessage(MESSAGES.jsonNonObjectError),
          title: formatMessage(MESSAGES.jsonInvalidError)
        })
        return null
      }

      return obj
    } catch (err) {
      setError({
        message: err.message,
        title: formatMessage(MESSAGES.jsonInvalidError)
      })
    }

    return null
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    event.stopPropagation()

    if (pipeline.isInputReadOnly) {
      return
    }

    setError(null)
    const obj = parseJson(currentValue, setError)
    if (obj === null) return

    if (view === DATA_VIEW) {
      // Generate avro schema from input
      try {
        // TODO: do not generate a new schema if the current one conforms the input
        const schema = generateSchema(obj)
        // Take pipeline name and remove forbidden characters
        const name = pipeline.name.replace(/[^a-zA-Z0-9]/g, '').replace(/^[-\d\s]*/g, '')
        schema.name = name.substring(0, 25)

        updatePipeline({ ...pipeline, schema, input: obj })
      } catch (err) {
        setError({
          message: err.message,
          title: formatMessage(MESSAGES.inputDataInvalidError)
        })
      }
    } else {
      // validate schema and generate a new input sample
      if (!obj.fields) {
        setError({
          message: formatMessage(MESSAGES.avroSchemaNonObjectError),
          title: formatMessage(MESSAGES.avroSchemaInvalidError)
        })
        return
      }

      try {
        // TODO: do not generate a new sample if the current one conforms the schema
        const input = randomInput(obj)

        updatePipeline({ ...pipeline, schema: obj, input })
      } catch (err) {
        setError({
          message: err.message,
          title: formatMessage(MESSAGES.avroSchemaGenericError)
        })
      }
    }
  }

  const placeholder = view === DATA_VIEW ? MESSAGES.inputDataPlaceholder : MESSAGES.avroSchemaPlaceholder
  const submitLabel = view === DATA_VIEW ? MESSAGES.inputDataSubmitButton : MESSAGES.avroSchemaSubmitButton

  const setValue = view === DATA_VIEW ? setInputStr : setSchemaStr
  const setError = view === DATA_VIEW ? setInputErr : setSchemaErr

  const currentObj = view === DATA_VIEW ? pipeline.input : pipeline.schema
  const currentValue = view === DATA_VIEW ? inputStr : schemaStr
  const currentError = view === DATA_VIEW ? inputErr : schemaErr

  let disableButtons = true
  try {
    disableButtons = deepEqual(JSON.parse(currentValue), currentObj)
  } catch (e) {
    disableButtons = false
  }

  return (
    <div className='section-body'>
      <div className='section-left'>
        <AvroSchemaViewer
          schema={pipeline.schema}
          highlight={highlight}
          pathPrefix='$'
          className='input-schema'
        />
      </div>

      <div className='section-right'>
        <h3 className='title-large'>
          <FormattedMessage
            id='input.title'
            defaultMessage='Define the source for your pipeline'
          />
        </h3>

        <div className='toggleable-content mt-3'>
          <ViewsBar
            current={view}
            setView={setView}
            views={[
              { id: SCHEMA_VIEW, label: formatMessage(MESSAGES.avroSchemaView) },
              { id: DATA_VIEW, label: formatMessage(MESSAGES.inputDataView) }
            ]}
          />

          <form onSubmit={handleSubmit}>
            {
              currentError &&
                <div className='textarea-header'>
                  <div className='hint error-message'>
                    <h4 className='hint-title'>
                      {currentError.title}
                    </h4>
                    {currentError.message}
                  </div>
                </div>
            }

            <textarea
              className={`monospace ${currentError ? 'error' : ''}`}
              required
              value={currentValue}
              onChange={(event) => {
                setValue(event.target.value)
                setError(null)
              }}
              placeholder={formatMessage(placeholder)}
              rows='10'
              disabled={pipeline.isInputReadOnly}
            />

            {
              !pipeline.isInputReadOnly &&
                <div className='action-buttons'>
                  <button
                    type='submit'
                    className='btn btn-w btn-primary mt-3'
                    disabled={disableButtons}
                  >
                    <span className='details-title'>
                      {formatMessage(submitLabel)}
                    </span>
                  </button>

                  <button
                    type='button'
                    className='btn btn-w btn-primary mt-3'
                    disabled={disableButtons}
                    onClick={() => {
                      setValue(objectToString(currentObj))
                      setError(null)
                    }}
                  >
                    <span className='details-title'>
                      <FormattedMessage
                        id='input.button.reset'
                        defaultMessage='Revert unsaved changes'
                      />
                    </span>
                  </button>
                </div>
            }
          </form>
        </div>
      </div>
    </div>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  pipeline: pipelines.currentPipeline,
  highlight: pipelines.currentContract && pipelines.currentContract.highlightSource
})
const mapDispatchToProps = { updatePipeline }

export default connect(mapStateToProps, mapDispatchToProps)(Input)
