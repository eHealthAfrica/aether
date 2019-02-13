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

import { PROJECT_NAME, getKernelURL } from '../utils/constants'
import { generateNewContract } from '../utils'
import { NavBar, Modal } from '../components'
import PublishButton from './PublishButton'
import InfoButton from './InfoButton'

import NewPipeline from './NewPipeline'
import {
  addPipeline,
  selectedPipelineChanged,
  getPipelines,
  fetchPipelines,
  addInitialContract,
  selectedContractChanged
} from './redux'

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
    this.props.getKernelURL()
  }

  componentDidMount () {
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
    if (nextProps.isNewPipeline && !nextProps.selectedPipeline.contracts.length) {
      const contractName = `${nextProps.selectedPipeline.name} - default contract`
      this.props.addInitialContract({ name: contractName, pipeline: nextProps.selectedPipeline.id })
    }
    if (nextProps.isNewPipeline && nextProps.selectedPipeline.contracts.length) {
      this.props.history.push(`/${nextProps.selectedPipeline.id}`)
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
        <div className={`preview-input ${pipeline.isInputReadOnly ? 'pipeline-readonly' : ''}`} onClick={this.onSelectPipeline.bind(this, pipeline)}>
          <div className='input-heading'>
            <span className='badge badge-c badge-big'>
              <i className='fas fa-file fa-sm' />
            </span>
            {pipeline.name}
          </div>
          <div className='info'>
            { pipeline.mappingset && <InfoButton pipeline={pipeline} /> }
          </div>
        </div>
        <div className='preview-contracts'>
          {
            pipeline.contracts.map(contract => (
              <React.Fragment key={contract.id}>
                <div className={`preview-contract ${contract.is_read_only ? 'pipeline-readonly' : ''}`}
                  onClick={() => { this.onSelectContract(pipeline, contract) }}>
                  <h2 className='contract-heading'>{contract.name}</h2>

                  <div className='contract-summaries'>
                    <div className='summary-entity-types'>
                      <span className='badge badge-b badge-big'>
                        { contract.entity_types ? contract.entity_types.length : 0 }
                      </span>
                      <FormattedMessage
                        id='pipeline.list.entity.types'
                        defaultMessage='Entity-Types'
                      />
                    </div>

                    <div className='summary-errors'>
                      <span className={`badge badge-b badge-big
                      ${contract && contract.mapping_errors.length && 'error'}`}>
                        { contract.mapping_errors ? contract.mapping_errors.length : 0 }
                      </span>
                      <FormattedMessage
                        id='contract.list.errors'
                        defaultMessage='Errors'
                      />
                    </div>
                  </div>

                  <div className='contract-publish'>
                    <div className='status-publish'>
                      <FormattedMessage
                        id='contract.list.publish-status'
                        defaultMessage={contract.published_on ? `Published on ${moment(contract.published_on).format('MMMM DD')}`
                          : 'Not published'}
                      />
                    </div>
                    <PublishButton pipeline={contract} className='btn btn-w btn-publish' />
                  </div>
                </div>
              </React.Fragment>
            ))
          }
          <button
            type='button'
            className='btn btn-c'
            onClick={this.onAddContract.bind(this, pipeline)}>
            <span className='details-title'>
              <FormattedMessage
                id='contract.add.button.add'
                defaultMessage='Add contract'
              />
            </span>
          </button>
        </div>
      </div>
    ))
  }

  onAddContract (pipeline) {
    this.props.selectedPipelineChanged(pipeline)
    this.props.selectedContractChanged(generateNewContract(pipeline))
    this.props.history.push({
      pathname: `/${pipeline.id}`,
      state: { createNewContract: true }
    })
  }

  onStartPipeline (newPipeline) {
    this.props.addPipeline(newPipeline)
  }

  onSelectContract (pipeline, contract) {
    this.props.selectedPipelineChanged(pipeline)
    this.props.selectedContractChanged(contract)
    this.props.history.push(`/${pipeline.id}/${contract.id}`)
  }

  onSelectPipeline (pipeline) {
    this.props.selectedPipelineChanged(pipeline)
    this.props.selectedContractChanged(pipeline.contracts.length && pipeline.contracts[0])
    this.props.history.push(`/${pipeline.id}`)
  }
}

const mapStateToProps = ({ pipelines }) => ({
  pipelineList: pipelines.pipelineList,
  error: pipelines.error,
  isNewPipeline: pipelines.isNewPipeline,
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, {
  getPipelines,
  selectedPipelineChanged,
  addPipeline,
  fetchPipelines,
  getKernelURL,
  addInitialContract,
  selectedContractChanged
})(PipelineList)
