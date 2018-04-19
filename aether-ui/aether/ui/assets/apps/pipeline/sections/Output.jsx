import React, { Component } from 'react'
import { connect } from 'react-redux'

class Output extends Component {
  render () {
    return (
      <div className='section-body'>
        <code>
          { JSON.stringify(this.props.selectedPipeline.output || [], 0, 2) }
        </code>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps)(Output)
