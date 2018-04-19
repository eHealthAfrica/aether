import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'
import avro from 'avro-js'

import { AvroSchemaViewer } from '../../components'

class Input extends Component {
  constructor (props) {
    super(props)

    this.state = {
      inputSchema: this.parseProps(props),
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
    return JSON.stringify(props.selectedPipeline.schema, 0, 2)
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
      const newSchema = JSON.parse(this.state.inputSchema)
      avro.parse(newSchema)

      this.props.onChange(newSchema)
    } catch (error) {
      this.setState({ error: error.message })
    }
  }

  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          <AvroSchemaViewer schema={this.props.selectedPipeline.schema} />
        </div>

        <div className='section-right'>
          <form onSubmit={this.notifyChange.bind(this)}>
            <label className='form-label'>
              <FormattedMessage
                id='input.empty.message'
                defaultMessage='Paste AVRO Schema'
              />
            </label>
            <FormattedMessage id='input.schema.placeholder' defaultMessage='Enter your schema'>
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

            { this.state.error &&
              <div className='hint'>
                <h4>
                  <FormattedMessage
                    id='pipeline.input.invalid.message'
                    defaultMessage='You have provided an invalid AVRO schema.'
                  />
                </h4>
                <br />
                { this.state.error }
              </div>
            }

            <button type='submit' className='btn btn-w btn-primary mt-3'>
              <span className='details-title'>
                <FormattedMessage
                  id='mapping.rule.button.ok'
                  defaultMessage='Add to pipeline'
                />
              </span>
            </button>
          </form>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps)(Input)
