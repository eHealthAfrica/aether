import React, { Component } from 'react'
import { connect } from 'react-redux'

class Output extends Component {
  render () {
    return (
      <div className='section-body'>
        <code>
          { JSON.stringify(this.props.output || [], 0, 2) }
        </code>
      </div>
    )
  }
}

export default connect()(Output)
