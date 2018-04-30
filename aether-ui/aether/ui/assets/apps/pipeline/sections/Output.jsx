import React, { Component } from 'react'
import { connect } from 'react-redux'

class Output extends Component {
  render () {
    return (
      <div className='section-body'>
        <div className='pipeline-errors'>
          <h3 className='title-medium'>Mapping Errors</h3>
          <code>
            { JSON.stringify(this.props.selectedPipeline.mapping_errors || [], 0, 2) }
          </code>
        </div>
        <div className='pipeline-data'>
          <h3 className='title-medium'>Output Data</h3>
          <code>
            { JSON.stringify(this.props.selectedPipeline.output || [], 0, 2) }
          </code>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps)(Output)
