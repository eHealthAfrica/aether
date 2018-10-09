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
import avro from 'avsc'

import { AvroSchemaViewer, Modal } from '../../components'
import {
  deepEqual,
  generateGUID,
  generateSchema
} from '../../utils'
import { updatePipeline, updateContract } from '../redux'

// The input section has two subviews `SCHEMA_VIEW` and `DATA_VIEW`.
// In the schema view, the user enters an avro schema representing their input.
// Sample data is derived from that schema and displayed in the `DataInput`
// component.
// In the data view, the user enters sample data representing a submission. An
// avro schema is derived from this sample and displayed in the `SchemaInput`.
const SCHEMA_VIEW = 'SCHEMA_VIEW'
const DATA_VIEW = 'DATA_VIEW'

export const isOptionalType = (type) => {
  return Array.isArray(type) && (type.indexOf('null') > -1)
}

export const makeOptionalType = (type) => {
  if (isOptionalType(type)) {
    return type
  }
  if (Array.isArray(type)) {
    return ['null', ...type]
  }
  return ['null', type]
}

export const makeOptionalField = (field) => {
  // The top-level "id" field is reserved for unique ids; do not make it
  // optional.
  if (field.name === 'id') { return field }
  return { ...field, type: makeOptionalType(field.type) }
}

export const deriveEntityTypes = (schema) => {
  const fields = schema.fields.map(makeOptionalField)
  return [{ ...schema, fields: fields }]
}

export const deriveMappingRules = (schema) => {
  const fieldToMappingRule = (field) => {
    return {
      id: generateGUID(),
      source: `$.${field.name}`,
      destination: `${schema.name}.${field.name}`
    }
  }
  return schema.fields.map(fieldToMappingRule)
}

const MESSAGES = defineMessages({
  recursiveError: {
    defaultMessage: 'Input data could not be generated from the schema provided. Recursive schemas are not supported.',
    id: 'pipeline.input.schema.invalid.message.head.recursive'
  },
  regularError: {
    defaultMessage: 'You have provided an invalid AVRO schema.',
    id: 'pipeline.input.schema.invalid.message.head'
  },

  idErrorMissing: {
    defaultMessage: 'The AVRO schema MUST have an "id" field with type "string".',
    id: 'pipeline.input.schema.invalid.message.id.missing'
  },
  idErrorType: {
    defaultMessage: 'The "id" field type MUST be "string".',
    id: 'pipeline.input.schema.invalid.message.id.type'
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
    this.setState({
      inputSchema: this.parseProps(nextProps)
    })
  }

  parseProps (props) {
    const { schema } = props.selectedPipeline
    return Object.keys(schema).length ? JSON.stringify(schema, 0, 2) : ''
  }

  onSchemaTextChanged (event) {
    this.setState({
      inputSchema: event.target.value
    })
  }

  notifyChange (event) {
    event.preventDefault()
    const { formatMessage } = this.props.intl
    this.setState({
      error: null,
      errorHead: null
    })
    try {
      // validate schema
      const schema = JSON.parse(this.state.inputSchema)
      const type = avro.parse(schema, { noAnonymousTypes: true })

      // check if there is an "id" field
      const idField = schema.fields.find(field => field.name === 'id')
      if (idField) {
        if (idField.type !== 'string') {
          // we enforce it to be string and not nullable
          this.setState({
            error: formatMessage(MESSAGES.idErrorType),
            errorHead: formatMessage(MESSAGES.regularError)
          })
          return
        }
      } else {
        this.setState({
          error: formatMessage(MESSAGES.idErrorMissing),
          errorHead: formatMessage(MESSAGES.regularError)
        })
        return
      }

      // generate a new input sample
      try {
        const input = type.random()
        input.id = generateGUID() // make it more UUID
        this.props.updatePipeline({ ...this.props.selectedPipeline, schema, input })
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
      return !deepEqual(schema, this.props.selectedPipeline.schema)
    } catch (e) {
      return true
    }
  }

  render () {
    return (
      <form onSubmit={this.notifyChange.bind(this)}>
        <div className='textarea-header'>
          {this.state.error &&
            <div className='hint error-message'>
              <h4 className='hint-title'>
                {this.state.errorHead}
              </h4>
              {this.state.error}
            </div>
          }
        </div>
        <FormattedMessage
          id='pipeline.input.schema.placeholder'
          defaultMessage='Paste an AVRO Schema and Sample Data will be generated for your convenience to use in the pipeline.'>
          {msg => (
            <textarea
              className={`monospace ${this.state.error ? 'error' : ''}`}
              required
              value={this.state.inputSchema}
              onChange={this.onSchemaTextChanged.bind(this)}
              placeholder={msg}
              rows='10'
              disabled={this.props.selectedPipeline.isInputReadOnly}
            />
          )}
        </FormattedMessage>

        <button type='submit' className='btn btn-w btn-primary mt-3' disabled={!this.hasChanged()}>
          <span className='details-title'>
            <FormattedMessage
              id='pipeline.input.schema.button.add'
              defaultMessage='Add to pipeline'
            />
          </span>
        </button>
        {this.state.inputSchema && !this.hasChanged() && <IdentityMapping {...this.props} />}
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
    const { input } = props.selectedPipeline
    return Object.keys(input).length ? JSON.stringify(input, 0, 2) : ''
  }

  onDataChanged (event) {
    this.setState({
      inputData: event.target.value
    })
  }

  notifyChange (event) {
    event.preventDefault()

    try {
      // Validate data and generate avro schema from input
      const input = JSON.parse(this.state.inputData)
      // check if there is an "id" field with an UUID content
      const schema = generateSchema({ id: generateGUID(), ...input })
      this.props.updatePipeline({
        ...this.props.selectedPipeline,
        schema,
        input
      })
    } catch (error) {
      this.setState({ error: error.message })
    }
  }

  hasChanged () {
    try {
      const schema = JSON.parse(this.state.inputData)
      return !deepEqual(schema, this.props.selectedPipeline.input)
    } catch (e) {
      return true
    }
  }

  render () {
    return (
      <form onSubmit={this.notifyChange.bind(this)}>
        <div className='textarea-header'>
          {this.state.error &&
            <div className='hint error-message'>
              <h4 className='hint-title'>
                <FormattedMessage
                  id='pipeline.input.data.invalid.message'
                  defaultMessage='Not a valid JSON document.'
                />
              </h4>
              {this.state.error}
            </div>
          }
        </div>
        <FormattedMessage
          id='pipeline.input.data.placeholder'
          defaultMessage='We will generate some sample data for you, once you have added a schema. Or, Add data in JSON Format and Aether will derive an AVRO schema for you.'>
          {msg => (
            <textarea
              className={`monospace ${this.state.error ? 'error' : ''}`}
              required
              value={this.state.inputData}
              onChange={this.onDataChanged.bind(this)}
              placeholder={msg}
              rows='10'
              disabled={this.props.selectedPipeline.isInputReadOnly}
            />
          )}
        </FormattedMessage>

        <button type='submit' className='btn btn-w btn-primary mt-3' disabled={this.props.selectedPipeline.isInputReadOnly || !this.hasChanged()}>
          <span className='details-title'>
            <FormattedMessage
              id='pipeline.input.data.button.add'
              defaultMessage='Derive schema from data'
            />
          </span>
        </button>
        {this.state.inputData && !this.hasChanged() && <IdentityMapping {...this.props} />}
      </form>
    )
  }
}

export class IdentityMapping extends Component {
  constructor (props) {
    super(props)
    this.state = {
      showModal: false
    }
    this.generateIdentityMapping = this.generateIdentityMapping.bind(this)
    this.hideModal = this.hideModal.bind(this)
    this.renderModal = this.renderModal.bind(this)
    this.showModal = this.showModal.bind(this)
  }

  showModal () {
    this.setState({ showModal: true })
  }

  hideModal () {
    this.setState({ showModal: false })
  }

  generateIdentityMapping () {
    const schema = this.props.selectedPipeline.schema
    const mappingRules = deriveMappingRules(schema)
    const entityTypes = deriveEntityTypes(schema)
    this.props.updateContract({
      ...this.props.selectedPipeline,
      mapping: mappingRules,
      entity_types: entityTypes
    })
    this.hideModal()
  }

  renderModal () {
    if (!this.state.showModal) { return null }
    const header = (
      <FormattedMessage
        id='pipeline.input.identityMapping.header'
        defaultMessage='Create passthrough pipeline'
      />
    )
    const content = (
      <FormattedMessage
        id='pipeline.input.identityMapping.content'
        defaultMessage='Are you sure that you want to create a passthrough pipeline? This action will overwrite all existing entity types and mappings.'
      />
    )
    const buttons = (
      <div>
        <button
          data-qa='input.identityMapping.btn-confirm'
          className='btn btn-w btn-primary'
          onClick={this.generateIdentityMapping}>
          <FormattedMessage
            id='pipeline.input.identityMapping.btn-confirm'
            defaultMessage='Yes'
          />
        </button>
        <button className='btn btn-w' onClick={this.hideModal}>
          <FormattedMessage
            id='pipeline.input.identityMapping.btn-cancel'
            defaultMessage='Cancel'
          />
        </button>
      </div>
    )
    return (
      <Modal
        show
        header={header}
        children={content}
        buttons={buttons}
      />
    )
  }

  render () {
    return (
      <div>
        <div className='identity-mapping'>
          <p>
            <FormattedMessage
              id='pipeline.input.identityMapping.btn-apply'
              defaultMessage='You can use a passthrough pipeline to leave submitted data unchanged. This will automatically create both Entity Types and Mappings.'
            />
          </p>
          <button
            data-qa='input.identityMapping.btn-apply'
            className='btn btn-w'
            onClick={this.showModal}
            disabled={this.props.selectedPipeline.is_read_only}
          >
            <FormattedMessage
              id='pipeline.input.identityMapping.btn-apply'
              defaultMessage='Create passthrough pipeline'
            />
          </button>
        </div>
        {this.renderModal()}
      </div>
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
            schema={this.props.selectedPipeline.schema}
            highlight={this.props.selectedPipeline.highlightSource}
          />
        </div>
        <div className='section-right'>
          <h3 className='title-large'>
            <FormattedMessage
              id='pipeline.input.title'
              defaultMessage='Define the source for your pipeline'
            />
          </h3>
          <div className='toggleable-content mt-3'>
            <div className='tabs'>
              <button
                className={`tab ${this.state.view === SCHEMA_VIEW ? 'selected' : ''}`}
                onClick={this.toggleInputView}>
                <FormattedMessage
                  id='pipeline.input.toggle.schema'
                  defaultMessage='Avro schema'
                />
              </button>
              <button
                className={`tab ${this.state.view === DATA_VIEW ? 'selected' : ''}`}
                onClick={this.toggleInputView}>
                <FormattedMessage
                  id='pipeline.input.toggle.data'
                  defaultMessage='JSON Data'
                />
              </button>
            </div>
            {this.state.view === SCHEMA_VIEW && <SchemaInput {...this.props} />}
            {this.state.view === DATA_VIEW && <DataInput {...this.props} />}
          </div>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, { updatePipeline, updateContract })(injectIntl(Input))
