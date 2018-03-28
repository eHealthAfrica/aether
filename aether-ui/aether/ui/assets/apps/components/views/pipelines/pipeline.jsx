import React, { Component } from 'react'
import { connect } from 'react-redux'

class PipeLine extends Component {

  render () {
    return (
      <div className='pipeline'>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(PipeLine)
