import React, { Component } from 'react'
import { connect } from 'react-redux'

class PipeLine extends Component {
  constructor (props) {
    super(props)
  }

  render () {
    return (
      <div className='pipeline'>
        <div className='pipeline-nav'>
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(PipeLine)
