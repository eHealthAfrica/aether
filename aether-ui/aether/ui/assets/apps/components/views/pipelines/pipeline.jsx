import React, { Component } from 'react'
import { connect } from 'react-redux'
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

  render () {
    return (
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
              <button
                className='btn-icon fullscreen-toggle'
                onClick={() => this.toggleFullscreen()}>{this.state.fullscreen ? 'close' : 'fullscreen'}</button>
            </div>
            <div
              className='pipeline-nav-item__mapping'
              onClick={() => this.setState({ pipelineView: 'mapping' })}>
              <div className='badge'>3</div>
              mapping
              <button
                className='btn-icon fullscreen-toggle'
                onClick={() => this.toggleFullscreen()}>{this.state.fullscreen ? 'close' : 'fullscreen'}</button>
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

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(PipeLine)
