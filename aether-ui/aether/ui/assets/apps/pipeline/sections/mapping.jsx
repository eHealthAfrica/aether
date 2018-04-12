import React, { Component } from 'react'
import { connect } from 'react-redux'

class Mapping extends Component {
  render () {
    return (
      <div className='section-body'>
        <div className='rules'>
          <h3>Mapping</h3>
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

export default connect(mapStateToProps, {})(Mapping)
