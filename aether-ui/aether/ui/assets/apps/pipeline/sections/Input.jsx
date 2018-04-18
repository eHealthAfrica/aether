import React, { Component } from 'react'
import { connect } from 'react-redux'
import { AvroSchemaViewer } from '../../components'
import { FormattedMessage } from 'react-intl'
import MockInputSchema from '../../mock/schema_input.mock'

class Input extends Component {
  constructor (props) {
    super(props)

    this.state = {
      inputSchema: JSON.stringify(MockInputSchema)
    }
  }

  onSchemaTextChanged (event) {
    this.setState({
      inputSchema: event.target.value
    })
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
              <textarea type='text' className='monospace' value={this.state.inputSchema}
                onChange={this.onSchemaTextChanged.bind(this)} placeholder={msg} rows='10' />
            )}
          </FormattedMessage>
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Input)
