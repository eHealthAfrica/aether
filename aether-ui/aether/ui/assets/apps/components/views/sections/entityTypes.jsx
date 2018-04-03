import React, { Component } from 'react'
import { connect } from 'react-redux'

class EntityTypes extends Component {
  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          <div className='hint hint-b'>
            No Entity Types added to your pipeline yet. 
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

export default connect(mapStateToProps, {})(EntityTypes)
