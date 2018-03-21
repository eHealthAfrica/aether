import React, { Component } from 'react'
import { connect } from 'react-redux'

class NewPipeLine extends Component {
  render () {
    return (
      <div>This is New Pipeline View</div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(NewPipeLine)
