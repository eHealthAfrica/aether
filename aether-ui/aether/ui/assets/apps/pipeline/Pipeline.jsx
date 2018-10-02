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
      showOutput: false,
      fullscreen: false
    }
  }

  componentDidMount () {
    if (!this.props.selectedPipeline) {
      if (this.props.match && this.props.match.params && this.props.match.params.cid) {
        this.props.getPipelineById(this.props.match.params.pid, this.props.match.params.cid)
      } else {
        this.props.history.replace('/')
      }
    }
  }

  componentWillReceiveProps (nextProps) {
    if (!nextProps.selectedPipeline) {
      this.props.history.replace('/')
    }
  }

  render () {
    const { selectedPipeline } = this.props
    if (!selectedPipeline) {
      return ''
    }
    return (
      <div className={`pipelines-container show-pipeline ${selectedPipeline.is_read_only ? 'selected-pipeline-readonly' : ''}`}>
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
            { selectedPipeline.is_read_only &&
              <span className='tag'>
                <FormattedMessage
                  id='pipeline.list.read-only'
                  defaultMessage='read-only'
                />
              </span>
            }
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
            { !this.props.selectedPipeline.is_read_only &&
              <PublishButton pipeline={this.props.selectedPipeline} className='btn btn-c btn-publish' />
            }
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
              { this.props.selectedPipeline.mapping.length > 0 &&
                <span className={`status ${this.props.selectedPipeline.mapping_errors.length > 0
                  ? 'red' : 'green'}`} /> }
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
