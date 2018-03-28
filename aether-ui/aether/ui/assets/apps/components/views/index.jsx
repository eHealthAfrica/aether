import React, { Component } from 'react'
import { connect } from 'react-redux'
import PipeLines from './pipelines/index'
import NewPipeLine from './pipelines/new_pipeline'
import PipeLine from './pipelines/pipeline'

class Home extends Component {

  constructor (props) {
    super(props)
    this.state = {
      view: 'show-index'
    }
  }
  render () {
    return (
      <div className={`pipelines-container ${this.state.view}`}>
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
          { this.state.view === 'show-pipeline' &&
            <div className='top-nav-breadcrumb'>
              <a 
                href='#'
                onClick={() => { this.setState({ view: 'show-index' }) }}>
                Pipelines
              </a>
              <span> // Name of pipeline</span>
            </div>
          }
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

        { this.state.view === 'show-index' &&
          <div className='pipelines'>
            <h1 className='pipelines-heading'>Project Name//Pipelines</h1>
            <NewPipeLine />
            { this.renderPipelinePreviews() }
          </div>
        }

        { this.state.view === 'show-pipeline' &&
          <PipeLine />
        }

      </div>
    )
  }

  renderPipelinePreviews() {
    return (
      <div className='pipeline-previews'>
        <div 
          onClick={() => { this.setState({ view: 'show-pipeline' }) }}
          className='pipeline-preview'>
          <h2 className='preview-heading'>Name of pipeline</h2>
          <div className='summary-entity-types'>
            <span className='badge badge-b badge-big'>5</span>
            Entity-Types
          </div>
          <div className='summary-errors'>
            <span className='badge badge-b badge-big'>0</span>
            Errors
          </div>
        </div>
        <div 
          onClick={() => { this.setState({ view: 'show-pipeline' }) }}
          className='pipeline-preview'>
          <h2 className='preview-heading'>longer name of pipeline</h2>
          <div className='summary-entity-types'>
            <span className='badge badge-b badge-big'>3</span>
            Entity-Types
          </div>
          <div className='summary-errors error'>
            <span className='badge badge-b badge-big'>2</span>
            Errors
          </div>
        </div>
      </div>
    )

  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(Home)
