import React, { Component } from 'react'
import { connect } from 'react-redux'

class Input extends Component {
  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          <div className='hint'>
            Your schema for this pipeline will be displayed here once you have added an AVRO schema.
          </div>
        </div>
        <div className='section-right'>
          <p>here is body text</p>
          <p>here is body text</p>
          <p>here is body text</p>
          <p>here is body text</p>
          <p>here is body text</p>
          <p>here is body text</p>
          <p>here is body text</p>
          <p>here is body text</p>
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Input)
