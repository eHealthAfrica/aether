import React, { Component } from 'react'
import { connect } from 'react-redux'

class Input extends Component {
  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          {this.props.children}
        </div>
        <div className='section-right'>
          <p>here is body text</p>
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Input)
