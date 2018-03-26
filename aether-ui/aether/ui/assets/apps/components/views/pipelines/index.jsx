import React, { Component } from 'react'
import { connect } from 'react-redux'

class PipeLines extends Component {
  render () {
    return (
      <div className='pipeline-previews'>
        <div className='pipeline-preview'>
          <h2 className='preview-heading'>Name of pipeline</h2>
          <div className='summary-entity-types'>
            <span className='badge badge-b badge-big'>5</span>
            Entity-Types
          </div>
          <div className='summary-errors'>
            <span className='badge badge-b badge-big'>0</span>
            Errors
          </div>
        </div>
        <div className='pipeline-preview'>
          <h2 className='preview-heading'>longer name of pipeline</h2>
          <div className='summary-entity-types'>
            <span className='badge badge-b badge-big'>3</span>
            Entity-Types
          </div>
          <div className='summary-errors error'>
            <span className='badge badge-b badge-big'>2</span>
            Errors
          </div>
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(PipeLines)
