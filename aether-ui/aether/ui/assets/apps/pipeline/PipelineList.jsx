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
import moment from 'moment'

import { PROJECT_NAME } from '../utils/constants'
import { NavBar, Modal } from '../components'
import PublishButton from './PublishButton'

import NewPipeline from './NewPipeline'
import { addPipeline, selectedPipelineChanged, getPipelines, fetchPipelines } from './redux'

class PipelineList extends Component {
  constructor (props) {
    super(props)
    this.state = {
      view: 'show-index',
      showError: false,
      errorHeader: '',
      errorMessage: ''
    }
  }

  componentWillMount () {
    if (!this.props.pipelineList.length) {
      this.props.getPipelines()
    }
    this.props.fetchPipelines()
  }

  componentWillReceiveProps (nextProps) {
    if (nextProps.error) {
      this.setState({
        showError: true,
        errorHeader: `Error code ${nextProps.error.status}`,
        errorMessage: nextProps.error.message
      })
    }
    if (nextProps.isNewPipeline) {
      this.props.history.push(`/${nextProps.pipelineList[0].id}`)
    }
  }

  setErrorModal (visible) {
    this.setState({ showError: visible })
  }

  render () {
    return (
      <div className={`pipelines-container ${this.state.view}`}>
        <NavBar />

        <div className='pipelines'>
          <h1 className='pipelines-heading'>
            { PROJECT_NAME }
            <span> // </span>
            <FormattedMessage
              id='pipeline.list.pipelines'
              defaultMessage='Pipelines'
            />
          </h1>
          <NewPipeline
            onStartPipeline={newPipeline => { this.onStartPipeline(newPipeline) }}
          />

          <div className='pipeline-previews'>
            { this.renderPipelineCards() }
          </div>
        </div>
      </div>
    )
  }

  renderPipelineCards () {
    return this.props.pipelineList.map(pipeline => (
      <div
        key={pipeline.id}
        className='pipeline-preview'>
        <Modal buttons={
          <button type='button' className='btn btn-w btn-primary' onClick={this.setErrorModal.bind(this, false)}>
            <FormattedMessage
              id='pipeline.modal.error.ok'
              defaultMessage='Ok'
            />
          </button>
        } header={this.state.errorHeader} show={this.state.showError}>
          {this.state.errorMessage}
        </Modal>
        <div
          onClick={() => { this.onSelectPipeline(pipeline) }}>
          <h2 className='preview-heading'>{pipeline.name}</h2>

          <div className='summary-entity-types'>
            <span className='badge badge-b badge-big'>
              { pipeline.entity_types ? pipeline.entity_types.length : 0 }
            </span>
            <FormattedMessage
              id='pipeline.list.entity.types'
              defaultMessage='Entity-Types'
            />
          </div>

          <div className='summary-errors'>
            <span className='badge badge-b badge-big'>
              { pipeline.mapping_errors ? pipeline.mapping_errors.length : 0 }
            </span>
            <FormattedMessage
              id='pipeline.list.errors'
              defaultMessage='Errors'
            />
          </div>
        </div>
        <div className='pipeline-publish'>
          <div className='status-publish'>
            <FormattedMessage
              id='pipeline.list.publish-status'
              defaultMessage={pipeline.published_on ? `Published on ${moment(pipeline.published_on).format('MMMM DD')}`
                : 'Not published'}
            />
          </div>
          <PublishButton pipeline={pipeline} className='btn btn-w btn-publish' />
        </div>

      </div>
    ))
  }

  onStartPipeline (newPipeline) {
    this.props.addPipeline(newPipeline)
  }

  onSelectPipeline (pipeline) {
    this.props.selectedPipelineChanged(pipeline)
    this.props.history.push(`/${pipeline.id}`)
  }
}

const mapStateToProps = ({ pipelines }) => ({
  pipelineList: pipelines.pipelineList,
  error: pipelines.error,
  isNewPipeline: pipelines.isNewPipeline
})

export default connect(mapStateToProps, { getPipelines, selectedPipelineChanged, addPipeline, fetchPipelines })(PipelineList)
