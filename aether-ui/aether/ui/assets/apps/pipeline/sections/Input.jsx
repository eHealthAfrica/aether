import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'
import { AvroSchemaViewer } from '../../components'

class Input extends Component {
  constructor (props) {
    super(props)

    this.state = {
      inputSchema: JSON.stringify(this.props.schema, 0, 2)
    }
  }

  componentWillReceiveProps (nextProps) {
    this.setState({
      inputSchema: JSON.stringify(this.props.schema, 0, 2)
    })
  }

  onSchemaTextChanged (event) {
    this.setState({
      inputSchema: event.target.value
    })
  }

  notifyChange (event) {
    const newSchema = JSON.parse(this.state.inputSchema)
    this.props.onChange(newSchema)
  }

  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          <AvroSchemaViewer schema={this.state.inputSchema} />
        </div>
        <div className='section-right'>
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
                value={this.state.inputSchema}
                onChange={this.onSchemaTextChanged.bind(this)}
                onBlur={this.notifyChange.bind(this)}
                placeholder={msg}
                rows='10'
              />
            )}
          </FormattedMessage>
        </div>
      </div>
    )
  }
}

export default connect()(Input)
