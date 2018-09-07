/*
 * Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

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
      showSettings: false,
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
      <div className={`pipelines-container show-pipeline pipeline--${this.state.pipelineView}`}>
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
        </NavBar>

        <div className={`pipeline ${this.state.showOutput ? 'show-output' : ''} ${this.state.fullscreen ? 'fullscreen' : ''}`}>
          <div className='pipeline-tabs'>
            <div className='pipeline-tab active'>
              {this.props.selectedPipeline.name}
              <span className='status green'></span>
              <div 
                className={`btn-icon settings-button ${this.state.showSettings ? 'active' : ''}`}
                onClick={() => this.toggleSettings()}>
                <i className='fas fa-ellipsis-h'/>
              </div>
            </div>
            <div className='pipeline-tab'>
              another contract
              <span className='status green'></span>
              <div 
                className='btn btn-d settings-button'
                onClick={() => this.toggleSettings()}>
                <i className='fas fa-ellipsis-h'/>
              </div>
            </div>

          </div>
          <div className='pipeline-nav'>
            <div className='pipeline-nav-items'>
              <div
                className='pipeline-nav-item__input'
                onClick={() => this.viewInput()}>
                <div className='badge'>
                  <i className='fas fa-file'/>
                </div>
                <FormattedMessage
                  id='pipeline.navbar.input'
                  defaultMessage='Input'
                />
              </div>
              <div
                className='pipeline-nav-item__entityTypes'
                onClick={() => this.setState({ pipelineView: 'entityTypes' })}>
                <div className='badge'>
                  <i className='fas fa-caret-right'/>
                </div>
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
                <div className='badge'>
                  <i className='fas fa-caret-right'/>
                </div>
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
              <div
                className='pipeline-nav-item__contracts'
                onClick={() => this.setState({ pipelineView: 'entityTypes' })}>
                <div className='badge'>                
                  <i className='fas fa-caret-right'/>
                </div>
                <FormattedMessage
                  id='pipeline.navbar.contracts'
                  defaultMessage='Contracts'
                />
              </div>
            </div>
            <div
              className='pipeline-nav-item__output'
              onClick={() => this.toggleOutput()}>
              <div className='badge'>                
                <i className='fas fa-caret-right'/>
              </div>
              <FormattedMessage
                id='pipeline.navbar.output'
                defaultMessage='Output'
              />
              { this.props.selectedPipeline.mapping.length > 0 &&
                <span className={`status ${this.props.selectedPipeline.mapping_errors.length > 0
                ? 'red' : 'green'}`} /> }
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

          { this.state.showSettings && 
            this.renderSettings()
          }

        </div>
      </div>
    )
  }

  toggleSettings () {
    if (!this.state.showSettings) {
      this.setState({ showSettings: true })
    } else {
      this.setState({ showSettings: false })
    }
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
      this.setState({ showOutput: false })
    } else {
      this.setState({ fullscreen: false })
    }
  }

  viewInput () {
    this.setState({ showOutput: false })
    this.setState({ pipelineView: 'input' })
  }


  renderSettings () {
    return (
      <div className='pipeline-settings'>
        <div
          className='btn-icon close-button'
          onClick={() => this.toggleSettings()}>
          <i className='fas fa-times'></i>
          <span>close settings</span>
        </div>

        <form className='contract-form'>
          <div className='form-group'>
            <label className='form-label'>
              <FormattedMessage
                id='contract.new.name'
                defaultMessage='Contract name'
              />
            </label>
            <input
              type='text'
              required
              name='name'
              className='input-d contract-name'
              placeholder={this.props.selectedPipeline.name}
            />
          </div>

          <div className='settings-section'>
            <label className='form-label'>
              <FormattedMessage
                id='settings.puplish.title'
                defaultMessage='Publish status'
              />
            </label>
            <div className='status-publish'>
              <FormattedMessage
                id='pipeline.publish-status'
                defaultMessage={this.props.selectedPipeline.published_on
                  ? `Published on ${moment(this.props.selectedPipeline.published_on).format('MMMM DD, YYYY HH:mm')}`
                  : 'Not published'}
              />
              <PublishButton pipeline={this.props.selectedPipeline} className='btn btn-d btn-publish' />
            </div>
            
            <label className='form-label'>
              <FormattedMessage
                id='settings.submission.title'
                defaultMessage='Submission URL'
              />
            </label>

            <a className='submission-url' href=''>blabla URL</a>
          </div>
          <button
            type='button'
            className='btn btn-d btn-big'>
            <span className='details-title'>
              <FormattedMessage
                id='pipeline.new.button.cancel'
                defaultMessage='Cancel'
              />
            </span>
          </button>
          <button
            type='submit'
            className='btn btn-d btn-primary btn-big ml-4'>
            <span className='details-title'>
              <FormattedMessage
                id='contract.save'
                defaultMessage='Save'
              />
            </span>
          </button>
        </form>

      </div>
    )

  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline,
  pipelineList: pipelines.pipelineList
})

export default connect(mapStateToProps, { getPipelineById, getPipelines })(Pipeline)
