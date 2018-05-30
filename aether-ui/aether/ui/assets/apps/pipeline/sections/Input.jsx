import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'
import avro from 'avsc'

import { AvroSchemaViewer, Modal } from '../../components'
import { generateGUID, deepEqual } from '../../utils'
import { generateSchemaName } from '../../utils/generateSchemaName'
import { updatePipeline } from '../redux'

// The input section has two subviews `SCHEMA_VIEW` and `DATA_VIEW`.
// In the schema view, the user enters an avro schema representing their input.
// Sample data is derived from that schema and displayed in the `DataInput`
// component.
// In the data view, the user enters sample data representing a submission. An
// avro schema is derived from this sample and displayed in the `SchemaInput`.
const SCHEMA_VIEW = 'SCHEMA_VIEW'
const DATA_VIEW = 'DATA_VIEW'

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

class SchemaInput extends Component {
  constructor (props) {
    super(props)
    this.state = {
      inputSchema: this.parseProps(props),
      view: SCHEMA_VIEW,
      error: null
    }
  }

  componentWillReceiveProps (nextProps) {
    this.setState({
      inputSchema: this.parseProps(nextProps),
      error: null
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

    try {
      // validate schema
      const schema = JSON.parse(this.state.inputSchema)
      const type = avro.parse(schema, { noAnonymousTypes: true })
      // generate a new input sample
      const input = type.random()
      this.props.updatePipeline({ ...this.props.selectedPipeline, schema, input })
    } catch (error) {
      this.setState({ error: error.message })
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
                <FormattedMessage
                  id='pipeline.input.schema.invalid.message'
                  defaultMessage='You have provided an invalid AVRO schema.'
                />
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
      const options = { typeHook: generateSchemaName('Auto') }
      const schema = avro.Type.forValue(input, options)
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
            />
          )}
        </FormattedMessage>

        <button type='submit' className='btn btn-w btn-primary mt-3' disabled={!this.hasChanged()}>
          <span className='details-title'>
            <FormattedMessage
              id='pipeline.input.data.button.add'
              defaultMessage='Derive schema from data'
            />
          </span>
        </button>
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
    this.generateIdentityMapping = this.generateIdentityMapping.bind(this)
    this.hideModal = this.hideModal.bind(this)
    this.renderModal = this.renderModal.bind(this)
    this.showModal = this.showModal.bind(this)
    this.toggleInputView = this.toggleInputView.bind(this)
  }

  showModal () {
    this.setState({showModal: true})
  }

  hideModal () {
    this.setState({showModal: false})
  }

  toggleInputView () {
    if (this.state.view === DATA_VIEW) {
      this.setState({ view: SCHEMA_VIEW })
    } else {
      this.setState({ view: DATA_VIEW })
    }
  }

  renderModal () {
    return (
      <div>
        <button onClick={this.generateIdentityMapping}>
          Yes
        </button>
        <button onClick={this.hideModal}>
          No
        </button>
      </div>
    )
  }

  generateIdentityMapping () {
    const schema = this.props.selectedPipeline.schema
    const mappingRules = deriveMappingRules(schema)
    const entityTypes = [schema]
    this.props.updatePipeline({
      ...this.props.selectedPipeline,
      mapping: mappingRules,
      entity_types: entityTypes
    })
    this.hideModal()
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

            <div className='identity-mapping'>
              <p>You can use Identity mapping for a 1:1 translation of your input into mappings. This will automatically create an Entity Type and its mappings.</p>
              <button className='btn btn-d' onClick={this.showModal}>
                Apply Identity Mapping
              </button>
            </div>

            <Modal show={this.state.showModal} buttons={this.renderModal()} />

          </div>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, { updatePipeline })(Input)
