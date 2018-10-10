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
import { PROJECT_NAME } from '../utils/constants'
import { publishPipeline, selectedPipelineChanged } from './redux'
import Modal from '../components/Modal'

class PublishButton extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showPublishOptions: false,
      publishOptionsButtons: null,
      publishOptionsContent: null
    }
  }

  componentWillReceiveProps (nextProps) {
    if (nextProps.selectedPipeline && nextProps.selectedPipeline.id &&
      nextProps.selectedPipeline.id === this.props.pipeline.id) {
      if (nextProps.publishError) {
        this.getPublishOptions('error', nextProps.publishError)
      }
      if (nextProps.publishSuccess) {
        this.getPublishOptions('success', nextProps.publishSuccess)
      }
    }
  }

  buildPublishErrors (errors) {
    const errorList = []
    errors.error.forEach(error => {
      errorList.push(<li key={error}>
        <FormattedMessage id={`publish.error.${error}`} defaultMessage={error} />
      </li>)
    })
    errors.exists.forEach(exists => {
      Object.keys(exists).forEach(exist => {
        errorList.push(<li key={exist}>
          <FormattedMessage id={`publish.exists.${exist}`} defaultMessage={exists[exist]} />
        </li>)
      })
    })
    return <ul className='error'>{errorList}</ul>
  }

  buildPublishSuccess () {
    return (<ul className='success'>
      <li key='publish_success_ok_'>
        <FormattedMessage id='publish.success.message' defaultMessage='Pipeline published successfully.' />
      </li>
    </ul>)
  }

  getPublishOptions (status, statusData) {
    this.setState({
      publishOptionsButtons: status === 'success' ? (
        <button type='button' className='btn btn-w btn-primary' onClick={this.setPublishOptionsModal.bind(this, false)}>
          <FormattedMessage
            id='publish.modal.sucess.ok'
            defaultMessage='Ok'
          />
        </button>
      ) : (
        <div>
          <button type='button' className='btn btn-w' onClick={this.setPublishOptionsModal.bind(this, false)}>
            <FormattedMessage
              id='publish.modal.cancel'
              defaultMessage='Cancel'
            />
          </button>
          {
            (!this.props.pipeline.mapping_errors || !this.props.pipeline.mapping_errors.length) && (<button type='button' className='btn btn-w btn-primary' onClick={this.publishOverwrite.bind(this)}>
              <FormattedMessage
                id='publish.modal.overwrite'
                defaultMessage='Overwrite Existing Pipeline'
              />
            </button>)
          }
        </div>
      ),
      showPublishOptions: true,
      publishOptionsContent: status === 'success' ? this.buildPublishSuccess() : this.buildPublishErrors(statusData)
    })
  }

  setPublishOptionsModal (visible) {
    this.setState({
      showPublishOptions: visible
    })
  }

  publishOverwrite () {
    this.setPublishOptionsModal(false)
    this.props.publishPipeline(this.props.pipeline.pipeline, this.props.pipeline.id, PROJECT_NAME, true, this.props.publishError.ids)
  }

  publish () {
    this.props.selectedPipelineChanged(this.props.pipeline)
    this.props.publishPipeline(this.props.pipeline.pipeline, this.props.pipeline.id)
  }

  render () {
    return (
      <div>
        <Modal show={this.state.showPublishOptions} header={`Publish ${this.props.pipeline.name}`}
          buttons={this.state.publishOptionsButtons}>
          {this.state.publishOptionsContent}
        </Modal>
        <button type='button' className={this.props.className} onClick={this.publish.bind(this)} disabled={this.props.disabled}>
          <FormattedMessage
            id='pipeline.navbar.breadcrumb.publish'
            defaultMessage='Publish pipeline'
          />
        </button>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  publishError: pipelines.publishError,
  publishSuccess: pipelines.publishSuccess,
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, { publishPipeline, selectedPipelineChanged })(PublishButton)
