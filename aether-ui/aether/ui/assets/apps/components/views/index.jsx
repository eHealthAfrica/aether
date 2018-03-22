import React, { Component } from 'react'
import { connect } from 'react-redux'
import { Link } from 'react-router-dom'
import PipeLines from './pipelines/index'

class Home extends Component {
  render () {
    return (
      <div>
        <div className='navbar'>
          <a className='navbar-brand' href='/' title='aether'>
            <div className='logo-container'>
              <div className='flipper'>
                <div className='front'>
                </div>
                <div className='back'>
                </div>
              </div>
            </div>
            <span data-app-name='app-name'>Aether</span>
          </a>
          <div className='nav-link user'>
            <span
              id='logged-in-user-info'>
              User name
            </span>
            <span className='logout'>
              <a href='#'><i className='fa fa-sign-out' title='Sign Out' aria-hidden='true' ></i></a>
            </span>
          </div>
        </div>
        <div>
          <h1>Project Name</h1>
          <Link to='/new-pipeline'>New Pipeline</Link>
          <PipeLines></PipeLines>
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Home)
