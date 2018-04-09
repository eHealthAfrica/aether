import React, { Component } from 'react'
import { connect } from 'react-redux'
import { Link } from 'react-router-dom'
import Input from '../sections/input'
import EntityTypes from '../sections/entityTypes'
import Mapping from '../sections/mapping'
import Output from '../sections/output'

class PipeLine extends Component {
  constructor (props) {
    super(props)
    this.state = {
      pipelineView: 'input',
      showOutput: false,
      fullscreen: false
    }
  }

  componentWillMount () {
    if (!this.props.selectedPipeline) {
      this.props.history.replace('/')
    }
  }

  render () {
    return (
      <div className={'pipelines-container show-pipeline'}>
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
          <div className='top-nav-breadcrumb'>
            <Link to='/'>
              <span>PIPELINES</span>
            </Link>
            <span> // {this.props.selectedPipeline ? this.props.selectedPipeline.name : 'Select a pipeline'}</span>
          </div>
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
        <div className={`pipeline pipeline--${this.state.pipelineView} ${this.state.showOutput ? 'show-output' : ''} ${this.state.fullscreen ? 'fullscreen' : ''}`}>
          <div className='pipeline-nav'>
            <div className='pipeline-nav-items'>
              <div
                className='pipeline-nav-item__input'
                onClick={() => this.setState({ pipelineView: 'input' })}>
                <div className='badge'>1</div>
                Input
              </div>
              <div
                className='pipeline-nav-item__entityTypes'
                onClick={() => this.setState({ pipelineView: 'entityTypes' })}>
                <div className='badge'>2</div>
                Entity Types
                <div
                  className='btn-icon fullscreen-toggle'
                  onClick={() => this.toggleFullscreen()}>
                  <span>{this.state.fullscreen ? 'close' : 'fullscreen'}</span>
                </div>
              </div>
              <div
                className='pipeline-nav-item__mapping'
                onClick={() => this.setState({ pipelineView: 'mapping' })}>
                <div className='badge'>3</div>
                mapping
                <div
                  className='btn-icon fullscreen-toggle'
                  onClick={() => this.toggleFullscreen()}>
                  <span>{this.state.fullscreen ? 'close' : 'fullscreen'}</span>
                </div>
              </div>
            </div>
            <div
              className='pipeline-nav-item__output'
              onClick={() => this.toggleOutput()}>
              <div className='badge badge-small' />
              output
              <div className='output-toggle' />
            </div>
          </div>

          <div className='pipeline-sections'>
            <div className='pipeline-section__input'>
              <Input />
            </div>
            <div className='pipeline-section__entityTypes'>
              <EntityTypes />
            </div>
            <div className='pipeline-section__mapping'>
              <Mapping />
            </div>
          </div>
          <div className='pipeline-output'>
            <Output />
          </div>
        </div>
      </div>
    )
  }

  toggleOutput () {
    if (!this.state.showOutput) {
      this.setState({ showOutput: true })
    } else {
      this.setState({ showOutput: false })
    }
  }
  toggleFullscreen () {
    if (!this.state.fullscreen) {
      this.setState({ fullscreen: true })
    } else {
      this.setState({ fullscreen: false })
    }
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, {})(PipeLine)
