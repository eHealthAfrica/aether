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

import { AvroSchemaViewer } from '../../components'
import { deepEqual, generateGUID } from '../../utils'
import { generateSchema, parseSchema } from '../../utils/avro-utils'

import { updatePipeline } from '../redux'

// The input section has two subviews `SCHEMA_VIEW` and `DATA_VIEW`.
// In the schema view, the user enters an avro schema representing their input.
// Sample data is derived from that schema and displayed in the `DataInput` component.
// In the data view, the user enters sample data representing a submission.
// An avro schema is derived from this sample and displayed in the `SchemaInput`.

const SCHEMA_VIEW = 'SCHEMA_VIEW'
const DATA_VIEW = 'DATA_VIEW'

const MESSAGES = defineMessages({
  recursiveError: {
    defaultMessage: 'Input data could not be generated from the schema provided. Recursive schemas are not supported.',
    id: 'input.schema.invalid.message.head.recursive'
  },
  regularError: {
    defaultMessage: 'You have provided an invalid AVRO schema.',
    id: 'input.schema.invalid.message.head'
  },
  inputDataPlaceholder: {
    defaultMessage: 'We will generate some sample data for you, once you have added a schema. Or, Add data in JSON Format and Aether will derive an AVRO schema for you.',
    id: 'input.data.placeholder'
  },
  inputSchemaPlacehoder: {
    defaultMessage: 'Paste an AVRO Schema and Sample Data will be generated for your convenience to use in the pipeline.',
    id: 'input.schema.placeholder'
  }
})

class SchemaInput extends Component {
  constructor (props) {
    super(props)

    this.state = {
      inputSchema: this.parseProps(props),
      view: SCHEMA_VIEW,
      error: null,
      errorHead: null
    }
  }

  componentWillReceiveProps (nextProps) {
    this.setState({ inputSchema: this.parseProps(nextProps) })
  }

  parseProps (props) {
    const { schema } = props.pipeline
    return Object.keys(schema).length ? JSON.stringify(schema, 0, 2) : ''
  }

  onSchemaTextChanged (event) {
    this.setState({ inputSchema: event.target.value })
  }

  notifyChange (event) {
    event.preventDefault()
    if (this.props.pipeline.isInputReadOnly) {
      return
    }

    this.setState({
      error: null,
      errorHead: null
    })

    const { formatMessage } = this.props.intl
    try {
      // validate schema
      const schema = JSON.parse(this.state.inputSchema)
      const type = parseSchema(schema)

      // generate a new input sample
      try {
        const input = type.random()
        // check if there is a string "id" field
        if (schema.fields.find(field => field.name === 'id' && field.type === 'string')) {
          input.id = generateGUID() // make it more UUID
        }
        this.props.updatePipeline({ ...this.props.pipeline, schema, input })
      } catch (error) {
        this.setState({
          error: error.message,
          errorHead: formatMessage(MESSAGES.recursiveError)
        })
      }
    } catch (error) {
      this.setState({
        error: error.message,
        errorHead: formatMessage(MESSAGES.regularError)
      })
    }
  }

  hasChanged () {
    try {
      const schema = JSON.parse(this.state.inputSchema)
      return !deepEqual(schema, this.props.pipeline.schema)
    } catch (e) {
      return true
    }
  }

  render () {
    const { formatMessage } = this.props.intl

    return (
      <form onSubmit={this.notifyChange.bind(this)}>
        <div className='textarea-header'>
          { this.state.error &&
            <div className='hint error-message'>
              <h4 className='hint-title'>
                { this.state.errorHead }
              </h4>
              { this.state.error }
            </div>
          }
        </div>

        <textarea
          className={`monospace ${this.state.error ? 'error' : ''}`}
          required
          value={this.state.inputSchema}
          onChange={this.onSchemaTextChanged.bind(this)}
          placeholder={formatMessage(MESSAGES.inputSchemaPlacehoder)}
          rows='10'
          disabled={this.props.pipeline.isInputReadOnly}
        />

        { !this.props.pipeline.isInputReadOnly &&
          <button type='submit' className='btn btn-w btn-primary mt-3' disabled={!this.hasChanged()}>
            <span className='details-title'>
              <FormattedMessage
                id='input.schema.button.add'
                defaultMessage='Add to pipeline'
              />
            </span>
          </button>
        }
      </form>
    )
  }
}

class DataInput extends Component {
  constructor (props) {
    super(props)
    this.state = {
      inputData: this.parseProps(props),
      error: null
    }
  }

  componentWillReceiveProps (nextProps) {
    this.setState({
      inputData: this.parseProps(nextProps),
      error: null
    })
  }

  parseProps (props) {
    const { input } = props.pipeline
    return Object.keys(input).length ? JSON.stringify(input, 0, 2) : ''
  }

  onDataChanged (event) {
    this.setState({ inputData: event.target.value })
  }

  notifyChange (event) {
    event.preventDefault()
    if (this.props.pipeline.isInputReadOnly) {
      return
    }

    try {
      // Validate data and generate avro schema from input
      const input = JSON.parse(this.state.inputData)
      const schema = generateSchema(input)

      this.props.updatePipeline({
        ...this.props.pipeline,
        schema,
        input
      })
    } catch (error) {
      this.setState({ error: error.message })
    }
  }

  hasChanged () {
    try {
      const data = JSON.parse(this.state.inputData)
      return !deepEqual(data, this.props.pipeline.input)
    } catch (e) {
      return true
    }
  }

  render () {
    const { formatMessage } = this.props.intl

    return (
      <form onSubmit={this.notifyChange.bind(this)}>
        <div className='textarea-header'>
          { this.state.error &&
            <div className='hint error-message'>
              <h4 className='hint-title'>
                <FormattedMessage
                  id='input.data.invalid'
                  defaultMessage='Not a valid JSON document.'
                />
              </h4>
              { this.state.error }
            </div>
          }
        </div>

        <textarea
          className={`monospace ${this.state.error ? 'error' : ''}`}
          required
          value={this.state.inputData}
          onChange={this.onDataChanged.bind(this)}
          placeholder={formatMessage(MESSAGES.inputDataPlaceholder)}
          rows='10'
          disabled={this.props.pipeline.isInputReadOnly}
        />

        { !this.props.pipeline.isInputReadOnly &&
          <button
            type='submit'
            className='btn btn-w btn-primary mt-3'
            disabled={this.props.pipeline.isInputReadOnly || !this.hasChanged()}>
            <span className='details-title'>
              <FormattedMessage
                id='input.data.button.add'
                defaultMessage='Derive schema from data'
              />
            </span>
          </button>
        }
      </form>
    )
  }
}

class Input extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showModal: false,
      view: DATA_VIEW
    }

    this.toggleInputView = this.toggleInputView.bind(this)
  }

  toggleInputView () {
    if (this.state.view === DATA_VIEW) {
      this.setState({ view: SCHEMA_VIEW })
    } else {
      this.setState({ view: DATA_VIEW })
    }
  }

  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          <AvroSchemaViewer
            schema={this.props.pipeline.schema}
            highlight={this.props.highlight}
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
            <div className='tabs'>
              <button
                className={`tab ${this.state.view === SCHEMA_VIEW ? 'selected' : ''}`}
                onClick={this.toggleInputView}>
                <FormattedMessage
                  id='input.toggle.schema'
                  defaultMessage='Avro schema'
                />
              </button>

              <button
                className={`tab ${this.state.view === DATA_VIEW ? 'selected' : ''}`}
                onClick={this.toggleInputView}>
                <FormattedMessage
                  id='input.toggle.data'
                  defaultMessage='JSON Data'
                />
              </button>
            </div>

            { this.state.view === SCHEMA_VIEW && <SchemaInput {...this.props} /> }
            { this.state.view === DATA_VIEW && <DataInput {...this.props} /> }
          </div>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  pipeline: pipelines.currentPipeline,
  highlight: pipelines.currentContract.highlightSource
})
const mapDispatchToProps = { updatePipeline }

export default connect(mapStateToProps, mapDispatchToProps)(injectIntl(Input))
