import React, { Component } from 'react'
import { connect } from 'react-redux'

class PipeLines extends Component {
  render () {
    return (
      <div>This is Pipeline's Home View</div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(PipeLines)
