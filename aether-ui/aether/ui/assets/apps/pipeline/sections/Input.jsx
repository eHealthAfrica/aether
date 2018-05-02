import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'
import avro from 'avsc'

import { AvroSchemaViewer } from '../../components'
import { deepEqual } from '../../utils'
import { generateSchemaName } from '../../utils/generateSchemaName'
import { updatePipeline } from '../redux'

const SCHEMA_VIEW = 'SCHEMA_VIEW'
const DATA_VIEW = 'DATA_VIEW'

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
        <label className='form-label'>
          <FormattedMessage
            id='pipeline.input.schema.empty.message'
            defaultMessage='Paste AVRO Schema'
          />
        </label>
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
        <FormattedMessage id='pipeline.input.schema.placeholder' defaultMessage='Enter your schema'>
          {msg => (
            <textarea
              className='monospace'
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

  onSchemaTextChanged (event) {
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
        <label className='form-label'>
          <FormattedMessage
            id='pipeline.input.data.empty.message'
            defaultMessage='Please paste data in JSON format. We will automatically derive an AVRO schema for you'
          />
        </label>
        {this.state.error &&
          <div className='hint error-message'>
            <h4 className='hint-title'>
              <FormattedMessage
                id='pipeline.input.data.invalid.message'
                defaultMessage='You have provided an invalid AVRO schema.'
              />
            </h4>
            {this.state.error}
          </div>
        }
        <FormattedMessage id='pipeline.input.data.placeholder' defaultMessage='Enter your data'>
          {msg => (
            <textarea
              className='monospace'
              required
              value={this.state.inputData}
              onChange={this.onSchemaTextChanged.bind(this)}
              placeholder={msg}
              rows='10'
            />
          )}
        </FormattedMessage>

        <button type='submit' className='btn btn-w btn-primary mt-3' disabled={!this.hasChanged()}>
          <span className='details-title'>
            <FormattedMessage
              id='pipeline.input.data.button.add'
              defaultMessage='Add to pipeline'
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
      view: DATA_VIEW
    }
  }

  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          <AvroSchemaViewer schema={this.props.selectedPipeline.schema} />
        </div>
        <div className='section-right'>
          <h3 className='title-large'>
            <FormattedMessage
              id='pipeline.input.title'
              defaultMessage='Define the source for your pipeline'
            />
          </h3>
          <div className='input-toggles'>
            <button 
              className={`btn btn-w ${this.state.view === SCHEMA_VIEW ? 'selected' : ''}`} 
              onClick={() => this.setState({ view: SCHEMA_VIEW })}>
              <FormattedMessage
                id='pipeline.input.toggle.schema'
                defaultMessage='Avro schema'
              />
            </button>
            <button 
              className={`btn btn-w ${this.state.view === DATA_VIEW ? 'selected' : ''}`} 
              onClick={() => this.setState({ view: DATA_VIEW })}>
              <FormattedMessage
                id='pipeline.input.toggle.data'
                defaultMessage='Data (JSON)'
              />
            </button>
          </div>

          {this.state.view === SCHEMA_VIEW && <SchemaInput {...this.props} />}
          {this.state.view === DATA_VIEW && <DataInput {...this.props} />}
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, { updatePipeline })(Input)
