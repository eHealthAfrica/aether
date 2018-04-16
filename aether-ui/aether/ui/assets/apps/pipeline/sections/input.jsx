import React, { Component } from 'react'
import { connect } from 'react-redux'
import { AvroSchemaViewer } from '../../components'
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
          <textarea type='text' value={this.state.inputSchema} onChange={this.onSchemaTextChanged.bind(this)} placeholder='Enter your schema'
            rows='10' />
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Input)
