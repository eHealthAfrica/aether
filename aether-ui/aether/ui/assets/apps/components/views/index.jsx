import React, { Component } from 'react'
import { connect } from 'react-redux'
import { Link } from 'react-router-dom'

class Home extends Component {
  render () {
    return (
      <div>
        This is AUX's Landing Page<br />
        <div>
          <Link to='/pipelines'>Pipelines</Link><br />
          <Link to='/new-pipeline'>New Pipeline</Link>
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Home)
