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
import { publishPipeline, selectedPipelineChanged, selectedContractChanged } from './redux'
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
    if (nextProps.selectedContract && nextProps.selectedContract.id &&
      nextProps.selectedContract.id === this.props.contract.id) {
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
    errors.error && errors.error.forEach(error => {
      errorList.push(<li key={error}>
        <FormattedMessage id={`publish.error.${error}`} defaultMessage={error} />
      </li>)
    })
    errors.exists && errors.exists.forEach(exists => {
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
    const ids = statusData.ids || {}
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
            (!this.props.contract.mapping_errors || !this.props.contract.mapping_errors.length) &&
            statusData.exists && (<button type='button' className='btn btn-w btn-primary' onClick={this.publishOverwrite.bind(this, ids)}>
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

  setPublishOptionsModal (visible, event) {
    event.stopPropagation()
    this.setState({
      showPublishOptions: visible
    })
  }

  publishOverwrite (ids, event) {
    event.stopPropagation()
    this.setPublishOptionsModal.bind(this, false)
    this.props.publishPipeline(this.props.pipeline.id, this.props.contract.id, PROJECT_NAME, true, ids)
  }

  publish (event) {
    event.stopPropagation()
    this.props.selectedPipelineChanged(this.props.pipeline)
    this.props.selectedContractChanged(this.props.contract)
    this.props.publishPipeline(this.props.pipeline.id, this.props.contract.id)
  }

  render () {
    return (
      <div>
        <Modal
          show={this.state.showPublishOptions}
          header={`Publish ${this.props.pipeline.name} | ${this.props.contract.name}`}
          buttons={this.state.publishOptionsButtons}
        >
          {this.state.publishOptionsContent}
        </Modal>
        <button type='button' className={this.props.className} onClick={this.publish.bind(this)} disabled={this.props.disabled}>
          <FormattedMessage
            id='pipeline.navbar.breadcrumb.publish'
            defaultMessage='Publish'
          />
        </button>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  publishError: pipelines.publishError,
  publishSuccess: pipelines.publishSuccess,
  selectedPipeline: pipelines.selectedPipeline,
  selectedContract: pipelines.selectedContract
})

export default connect(mapStateToProps, {
  publishPipeline,
  selectedPipelineChanged,
  selectedContractChanged
})(PublishButton)
