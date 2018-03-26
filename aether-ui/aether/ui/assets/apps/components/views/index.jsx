import React, { Component } from 'react'
import { connect } from 'react-redux'
import PipeLines from './pipelines/index'
import NewPipeLine from './pipelines/new_pipeline'

class Home extends Component {
  render () {
    return (
      <div className='pipelines-container'>
        <div className='navbar top-nav'>
          <a className='top-nav-logo' href='/' title='aether'>
            <div className='logo-container'>
              <div className='flipper'>
                <div className='front' />
                <div className='back' />
              </div>
            </div>
            <span data-app-name='app-name'><b>ae</b>ther</span>
          </a>
          <div className='top-nav-user'>
            <span
              id='logged-in-user-info'>
              User name
            </span>
            <span className='logout'>
              <a href='#'><i className='fa fa-sign-out' title='Sign Out' aria-hidden='true' /></a>
            </span>
          </div>
        </div>
        <div className='pipelines'>
          <h1 className='pipelines-heading'>Project Name//Pipelines</h1>
          <NewPipeLine />
          <PipeLines />
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Home)
