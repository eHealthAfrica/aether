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

import { NavBar, Modal } from '../components'
import PublishButton from './PublishButton'

import Input from './sections/Input'
import EntityTypes from './sections/EntityTypes'
import Mapping from './sections/Mapping'
import Output from './sections/Output'
import {
  getPipelineById,
  getPipelines,
  selectedContractChanged,
  updateContract,
  addInitialContract
} from './redux'
import { getKernelURL } from '../utils/constants'
import { generateNewContract } from '../utils'

class Pipeline extends Component {
  constructor (props) {
    super(props)
    this.state = {
      pipelineView: 'input',
      showSettings: false,
      showOutput: false,
      fullscreen: false,
      newContracts: [],
      contractName: '',
      pipelineTabs: null,
      errorMessage: '',
      errorHeader: '',
      showError: false
    }
  }

  componentDidMount () {
    this.props.getKernelURL()
    const { match } = this.props
    if (!this.props.selectedPipeline) {
      if (match && match.params && match.params.pid) {
        this.props.getPipelineById(match.params.pid, match.params.cid)
      } else {
        this.props.history.replace('/')
      }
    }
    if (!this.props.selectedContract && this.props.selectedPipeline) {
      this.props.selectedContractChanged(this.props.selectedPipeline.contracts[0] || null)
    }

    if (this.props.location.state && this.props.location.state.createNewContract) {
      this.setState({
        pipelineView: 'entityTypes',
        newContracts: [...this.state.newContracts, this.props.selectedContract]
      }, () => this.renderNewContractTabs(this.state.newContracts))
      this.toggleSettings()
    }

    if (match && match.params && match.params.cid) {
      this.setDefaultContract(match.params.cid)
    }
  }

  componentDidUpdate (prevProps) {
    if (prevProps.selectedContract !== this.props.selectedContract) {
      this.setState({
        contractName: this.props.selectedContract.name
      })
    }
    if (prevProps.selectedPipeline !== this.props.selectedPipeline) {
      this.renderTabs(this.props.selectedPipeline.contracts, this.props.selectedContract)
    }
    if (this.props.error && prevProps.error !== this.props.error) {
      this.setState({
        showError: true,
        errorHeader: `Error code ${this.props.error.status}`,
        errorMessage: this.props.error.message
      })
      if (!this.props.selectedContract.id) {
        const floatingContract = { ...this.props.selectedContract }
        this.setState({
          newContracts: [floatingContract],
          showSettings: true
        })
        this.renderNewContractTabs([floatingContract])
      }
    }
  }

  setDefaultContract (contractId) {
    if (this.props.selectedPipeline) {
      const selectedContract = this.props.selectedPipeline.contracts
        .find(x => x.id === contractId)
      if (selectedContract) {
        this.props.selectedContractChanged(selectedContract)
        this.setState({ pipelineView: 'entityTypes' })
      }
    }
  }

  onTabChange (contract) {
    this.props.selectedContractChanged(contract)
  }

  renderTabs (contracts, selectedContract) {
    return (
      <React.Fragment>
        {
          contracts.map(contract => (
            <div className={`pipeline-tab ${selectedContract.name === contract.name ? 'active' : ''}`}
              onClick={this.onTabChange.bind(this, contract)}
              key={contract.id}>
              {contract.name}
              {contract.mapping.length ? <span className={`status ${contract.mapping_errors.length ? 'red' : 'green'}`} /> : null}
              <div
                className={`btn-icon settings-button ${this.state.showSettings ? 'active' : ''}`}
                onClick={() => this.toggleSettings()}>
                <i className='fas fa-ellipsis-h' />
              </div>
            </div>
          ))
        }
      </React.Fragment>
    )
  }

  renderNewContractTabs (contracts) {
    this.setState({
      newContractTabs: (
        <React.Fragment>
          {
            contracts.length ? contracts.map(contract => (
              <div className={`pipeline-tab ${this.props.selectedContract && this.props.selectedContract.name === contract.name ? 'active' : ''}`}
                key={contract.name}
                onClick={this.onTabChange.bind(this, contract)}
              >
                {contract.name}
              </div>
            )) : null
          }
        </React.Fragment>
      )
    })
  }

  setErrorModal (visible) {
    this.setState({
      showError: visible
    })
  }

  render () {
    const { selectedPipeline } = this.props
    let firstContract = {}
    if (!selectedPipeline) {
      return ''
    } else {
      firstContract = selectedPipeline.contracts[0] || {}
    }
    return (
      <div className={`pipelines-container show-pipeline pipeline--${this.state.pipelineView}`}>
        <Modal buttons={
          <button type='button' className='btn btn-w btn-primary' onClick={this.setErrorModal.bind(this, false)}>
            <FormattedMessage
              id='single.pipeline.modal.error.ok'
              defaultMessage='Ok'
            />
          </button>
        } header={this.state.errorHeader} show={this.state.showError}>
          {this.state.errorMessage}
        </Modal>
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
            { selectedPipeline.isInputReadOnly &&
              <span className='tag'>
                <FormattedMessage
                  id='selected-pipeline.read-only.indicator'
                  defaultMessage='read-only'
                />
              </span>
            }
          </div>
        </NavBar>

        <div className={`pipeline ${this.state.showOutput ? 'show-output' : ''} ${this.state.fullscreen ? 'fullscreen' : ''}`}>
          <div className='pipeline-tabs'>
            {
              this.renderTabs(this.props.selectedPipeline.contracts, this.props.selectedContract)
            }
            {
              this.state.newContractTabs
            }
            <button
              type='button'
              className='btn btn-c btn-sm new-contract'
              onClick={this.addNewContract.bind(this)}
            >
              <span className='details-title'>
                <FormattedMessage
                  id='contract.add.button.add'
                  defaultMessage='Add contract'
                />
              </span>
            </button>

          </div>
          <div className='pipeline-nav'>
            <div className='pipeline-nav-items'>
              <div
                className='pipeline-nav-item__input'
                onClick={() => this.viewInput()}>
                <div className='badge'>
                  <i className='fas fa-file' />
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
                  <i className='fas fa-caret-right' />
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
                  <i className='fas fa-caret-right' />
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
                  <i className='fas fa-caret-right' />
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
                <i className='fas fa-caret-right' />
              </div>
              <FormattedMessage
                id='pipeline.navbar.output'
                defaultMessage='Output'
              />
              {
                this.props.selectedContract.mapping.length > 0 && <span
                  className={`status ${this.props.selectedContract.mapping_errors.length ? 'red' : 'green'}`}
                />
              }
            </div>
          </div>

          <div className='pipeline-sections'>
            <div className='pipeline-section__input'>
              <Input />
            </div>
            <div className='pipeline-section__entityTypes'>
              <EntityTypes contract={this.props.selectedContract || firstContract} />
            </div>
            <div className='pipeline-section__mapping'>
              <Mapping contract={this.props.selectedContract || firstContract} />
            </div>
          </div>
          <div className='pipeline-output'>
            <Output contract={this.props.selectedContract || firstContract} />
          </div>

          { this.state.showSettings &&
            this.renderSettings()
          }

        </div>
      </div>
    )
  }

  addNewContract () {
    const nContract = generateNewContract(this.props.selectedPipeline, this.state.newContracts)
    this.props.selectedContractChanged(nContract)
    this.setState({
      newContracts: [...this.state.newContracts, nContract],
      showSettings: true
    }, () => this.renderNewContractTabs(this.state.newContracts))
  }

  toggleSettings () {
    if (!this.state.showSettings) {
      this.setState({ showSettings: true, contractName: this.props.selectedContract.name })
    } else {
      if (!this.props.selectedContract.id) {
        this.setState({
          newContracts: []
        })
        this.renderNewContractTabs([])
      }
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
      this.setState({
        fullscreen: true,
        showOutput: false
      })
    } else {
      this.setState({ fullscreen: false })
    }
  }

  viewInput () {
    this.setState({
      showOutput: false,
      pipelineView: 'input',
      showSettings: false
    })
  }

  onSettingsSave () {
    const { selectedContract } = this.props
    if (!selectedContract.id) {
      const newContract = { ...selectedContract, pipeline: this.props.selectedPipeline.id, name: this.state.contractName }
      this.props.addInitialContract(newContract)
      this.setState({
        newContracts: []
      })
      this.renderNewContractTabs([])
    } else {
      this.props.updateContract({ ...selectedContract, name: this.state.contractName })
    }
    this.toggleSettings()
  }

  renderSettings () {
    return (
      <div className='pipeline-settings'>
        <div
          className='btn-icon close-button'
          onClick={() => this.toggleSettings()}>
          <i className='fas fa-times' />
          <span>close settings</span>
        </div>

        <div className='contract-form'>
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
              value={this.state.contractName}
              onChange={e => this.setState({ contractName: e.target.value })}
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
                defaultMessage={this.props.selectedContract.published_on
                  ? `Published on ${moment(this.props.selectedContract.published_on).format('MMMM DD, YYYY HH:mm')}`
                  : 'Not published'}
              />
              <PublishButton pipeline={this.props.selectedPipeline} className='btn btn-d btn-publish' />
            </div>
            { this.props.selectedContract.published_on
              ? <div>
                <label className='form-label'>
                  <FormattedMessage
                    id='settings.submission.title'
                    defaultMessage='Submission URL'
                  />
                </label>

                <a className='submission-url'
                  href={`${this.props.kernelUrl}/submissions/?mappingset=${this.props.selectedPipeline.mappingset}`}>
                  {this.props.selectedPipeline.mappingset &&
                  `${this.props.kernelUrl}/submissions/?mappingset=${this.props.selectedPipeline.mappingset}`}</a>
              </div> : null
            }
          </div>
          <button
            onClick={() => this.toggleSettings()}
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
            className='btn btn-d btn-primary btn-big ml-4'
            onClick={this.onSettingsSave.bind(this)}>
            <span className='details-title'>
              <FormattedMessage
                id='contract.save'
                defaultMessage='Save'
              />
            </span>
          </button>
        </div>

      </div>
    )
  }
}

const mapStateToProps = ({ pipelines, constants }) => ({
  selectedPipeline: pipelines.selectedPipeline,
  pipelineList: pipelines.pipelineList,
  selectedContract: pipelines.selectedContract,
  kernelUrl: constants.kernelUrl,
  error: pipelines.error
})

export default connect(mapStateToProps, {
  getPipelineById,
  getPipelines,
  selectedContractChanged,
  getKernelURL,
  updateContract,
  addInitialContract
})(Pipeline)
