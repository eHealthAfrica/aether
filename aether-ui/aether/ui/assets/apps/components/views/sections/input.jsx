import React, { Component } from 'react'
import { connect } from 'react-redux'

class Input extends Component {
  render () {
    return (
      <div className='section-body'>
        <h3>input</h3>
        <p>here is body text</p>
        <p>here is body text</p>
        <p>here is body text</p>
        <p>here is body text</p>
        <p>here is body text</p>
        <p>here is body text</p>
        <p>here is body text</p>
        <p>here is body text</p>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Input)
