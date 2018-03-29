import React, { Component } from 'react'
import { connect } from 'react-redux'

class PipeLine extends Component {
  constructor (props) {
    super(props)
    this.state = {
      pipelineView: 'input',
      showOutput: false
    }
  }

  render () {
    return (
      <div className={`pipeline pipeline--${this.state.pipelineView} ${this.state.showOutput ? 'show-output' : ''}`}>
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
            </div>
            <div
              className='pipeline-nav-item__mapping'
              onClick={() => this.setState({ pipelineView: 'mapping' })}>
              <div className='badge'>3</div>
              mapping
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
          <div className='pipeline-section__input'>input</div>
          <div className='pipeline-section__entityTypes'>entity types</div>
          <div className='pipeline-section__mapping'>mapping</div>
        </div>
        <div className='pipeline-output'>output</div>
      </div>
    )
  }

  toggleOutput () {
    console.log(this.state.showOutput)
    if (!this.state.showOutput) {
      this.setState({ showOutput: true })
    } else {
      this.setState({ showOutput: false })
    }
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(PipeLine)
