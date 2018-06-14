import React, { Component } from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'
import { Link } from 'react-router-dom'
import moment from 'moment'

import { NavBar } from '../components'
import PublishButton from './PublishButton'
import InfoButton from './InfoButton'

import Input from './sections/Input'
import EntityTypes from './sections/EntityTypes'
import Mapping from './sections/Mapping'
import Output from './sections/Output'
import { getPipelineById, getPipelines } from './redux'

class Pipeline extends Component {
  constructor (props) {
    super(props)

    this.state = {
      pipelineView: 'input',
      showOutput: false,
      fullscreen: false
    }
  }

  componentDidMount () {
    if (this.props.match && this.props.match.params && this.props.match.params.id) {
      if (!this.props.selectedPipeline) {
        if (this.props.pipelineList.length) {
          this.props.getPipelineById(this.props.match.params.id)
        } else {
          this.props.getPipelines()
        }
      }
    }
  }

  componentWillReceiveProps (nextProps) {
    if (this.props.match.params.id !== nextProps.match.params.id) {
      this.props.getPipelineById(nextProps.match.params.id)
    }
    if (nextProps.pipelineList !== this.props.pipelineList && !this.props.selectedPipeline) {
      this.props.getPipelineById(this.props.match.params.id)
    }
    if (!nextProps.selectedPipeline && this.props.pipelineList.length) {
      this.props.history.replace('/')
    }
    if (!this.props.pipelineList.length && !nextProps.pipelineList.length) {
      this.props.history.replace('/')
    }
  }

  render () {
    const {selectedPipeline} = this.props
    if (!selectedPipeline) {
      return ''
    }

    return (
      <div className={'pipelines-container show-pipeline'}>
        <NavBar showBreadcrumb>
          <div className='breadcrumb-links'>
            <Link to='/'>
              <FormattedMessage
                id='pipeline.navbar.breadcrumb.pipelines'
                defaultMessage='Pipelines'
              />
            </Link>
            <span> // </span>
            { selectedPipeline.name }
          </div>
          <div className='top-nav-publish'>
            <div className='status-publish'>
              <FormattedMessage
                id='pipeline.publish-status'
                defaultMessage={this.props.selectedPipeline.published_on
                  ? `Published on ${moment(this.props.selectedPipeline.published_on).format('MMMM DD, YYYY HH:mm')}`
                  : 'Not published'}
              />
              {this.props.selectedPipeline.published_on && 
                <InfoButton pipeline={this.props.selectedPipeline} />
              }
            </div>
            <PublishButton pipeline={this.props.selectedPipeline} className='btn btn-c btn-publish' />
          </div>
        </NavBar>

        <div className={`pipeline pipeline--${this.state.pipelineView} ${this.state.showOutput ? 'show-output' : ''} ${this.state.fullscreen ? 'fullscreen' : ''}`}>
          <div className='pipeline-nav'>
            <div className='pipeline-nav-items'>
              <div
                className='pipeline-nav-item__input'
                onClick={() => this.setState({ pipelineView: 'input' })}>
                <div className='badge'>1</div>
                <FormattedMessage
                  id='pipeline.navbar.input'
                  defaultMessage='Input'
                />
              </div>
              <div
                className='pipeline-nav-item__entityTypes'
                onClick={() => this.setState({ pipelineView: 'entityTypes' })}>
                <div className='badge'>2</div>
                <FormattedMessage
                  id='pipeline.navbar.entity.types'
                  defaultMessage='Entity Types'
                />
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
                <FormattedMessage
                  id='pipeline.navbar.mapping'
                  defaultMessage='Mapping'
                />
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
              <FormattedMessage
                id='pipeline.navbar.output'
                defaultMessage='Output'
              />
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
  selectedPipeline: pipelines.selectedPipeline,
  pipelineList: pipelines.pipelineList
})

export default connect(mapStateToProps, { getPipelineById, getPipelines })(Pipeline)
