/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

import { LoadingSpinner, Modal, ModalError, NavBar } from '../components'

import Input from './sections/Input'
import EntityTypes from './sections/EntityTypes'
import Mapping from './sections/Mapping'
import Output from './sections/Output'
import Settings from './sections/Settings'
import DeleteModal from './components/DeleteModal'
import DeleteStatus from './components/DeleteStatus'

import {
  clearSelection,
  getPipelineById,
  selectContract,
  selectSection,
  deleteContract
} from './redux'

import {
  PIPELINE_SECTION_INPUT,
  CONTRACT_SECTION_ENTITY_TYPES,
  CONTRACT_SECTION_MAPPING,
  CONTRACT_SECTION_SETTINGS
} from '../utils/constants'

class Pipeline extends Component {
  constructor (props) {
    super(props)

    const view = props.section || props.match.params.section || PIPELINE_SECTION_INPUT

    this.state = {
      deleteOptions: {},
      fullscreen: false,
      isNew: props.location.state && props.location.state.isNewContract,
      newContract: null,
      showCancelModal: false,
      showDeleteModal: false,
      showDeleteProgress: false,
      showSettings: (view === CONTRACT_SECTION_SETTINGS),
      showOutput: false,
      onContractSavedCallback: null,
      view: (view === CONTRACT_SECTION_SETTINGS) ? CONTRACT_SECTION_ENTITY_TYPES : view
    }

    this.handleAddNewContract = this.handleAddNewContract.bind(this)
    this.deleteContract = this.deleteContract.bind(this)
    this.hideModalProgress = this.hideModalProgress.bind(this)
    this.handleBackToPipelines = this.handleBackToPipelines.bind(this)
    this.handleCancelContract = this.handleCancelContract.bind(this)
    this.handleContracts = this.handleContracts.bind(this)
    this.onContractTabSelected = this.onContractTabSelected.bind(this)
    this.handleDeleteContract = this.handleDeleteContract.bind(this)
    this.handleInput = this.handleInput.bind(this)
    this.handleCreateNewContract = this.handleCreateNewContract.bind(this)
    this.handleSave = this.handleSave.bind(this)
    this.handleCloseSettings = this.handleCloseSettings.bind(this)
  }

  componentDidMount () {
    // load current pipeline using location address (router props)
    if (!this.state.isNew) {
      this.props.getPipelineById(this.props.match.params.pid)
    } else {
      this.handleAddNewContract()
    }
  }

  componentDidUpdate (prevProps) {
    if (
      !this.state.isNew &&
      this.props.contract &&
      (
        prevProps.section !== this.props.section ||
        (prevProps.contract && prevProps.contract.id !== this.props.contract.id)
      )
    ) {
      // update router history
      this.props.history.push(
        `/${this.props.pipeline.id}/${this.props.contract.id}/${this.props.section}`
      )
    }

    // persist in-memory new contract
    if (this.state.isNew && this.props.contract && this.props.contract !== this.state.newContract) {
      this.setState({
        newContract: this.props.contract
      })
    }

    if (prevProps.section !== this.props.section) {
      // update state
      if (this.props.section === PIPELINE_SECTION_INPUT) {
        return this.setState({
          view: this.props.section,
          showSettings: false,
          showOutput: false,
          fullscreen: false
        })
      }

      if (this.props.section === CONTRACT_SECTION_SETTINGS) {
        return this.setState({
          view: this.state.view === PIPELINE_SECTION_INPUT
            ? CONTRACT_SECTION_ENTITY_TYPES
            : this.state.view,
          showSettings: true,
          showOutput: false
        })
      }

      return this.setState({
        view: this.props.section,
        showSettings: false
      })
    }
  }

  handleBackToPipelines () {
    this.checkUnsavedContract(() => {
      this.props.history.push('/')
      this.props.clearSelection()
    })
  }

  checkUnsavedContract (cb) {
    if (this.state.newContract) {
      this.setState({
        showCancelModal: true,
        onContractSavedCallback: cb
      })
    } else {
      this.setState({
        showCancelModal: false
      }, () => { cb && cb() })
    }
  }

  render () {
    const { pipeline } = this.props
    if (!pipeline) {
      return <LoadingSpinner /> // still loading data
    }

    const fullscreenDiv = (
      <div
        className='btn-icon fullscreen-toggle'
        onClick={() => { this.setState({ fullscreen: !this.state.fullscreen }) }}
      >
        {
          this.state.fullscreen
            ? <FormattedMessage id='pipeline.navbar.shrink' defaultMessage='fullscreen off' />
            : <FormattedMessage id='pipeline.navbar.fullscreen' defaultMessage='fullscreen on' />
        }
      </div>
    )

    return (
      <div className={`pipelines-container show-pipeline pipeline--${this.state.view}`}>
        {this.props.loading && <LoadingSpinner />}
        {this.props.error && <ModalError error={this.props.error} />}
        <NavBar showBreadcrumb onClick={this.handleBackToPipelines}>
          <div className='breadcrumb-links'>
            <a onClick={this.handleBackToPipelines}>
              <FormattedMessage
                id='pipeline.navbar.pipelines'
                defaultMessage='Pipelines'
              />
            </a>
            <span className='breadcrumb-pipeline-name'>
              <span>// </span>
              {pipeline.name}
              {
                pipeline.isInputReadOnly &&
                  <span className='tag'>
                    <FormattedMessage
                      id='pipeline.navbar.read-only'
                      defaultMessage='read-only'
                    />
                  </span>
              }
            </span>
          </div>
        </NavBar>

        <div className={`
          pipeline
          ${this.state.showOutput ? 'show-output' : ''}
          ${this.state.fullscreen ? 'fullscreen' : ''}
        `}
        >
          <div className='pipeline-tabs'>
            {this.renderContractTabs()}
            {this.renderNewContractTab()}
            {
              !this.state.newContract &&
                <button
                  type='button'
                  className='btn btn-c btn-sm new-contract'
                  onClick={this.handleAddNewContract}
                >
                  <span className='details-title'>
                    <FormattedMessage
                      id='contract.add.button'
                      defaultMessage='Add contract'
                    />
                  </span>
                </button>
            }
          </div>

          {this.renderSectionTabs()}

          {
            this.state.showSettings &&
              <Settings
                onClose={this.handleCloseSettings}
                isNew={this.state.isNew}
                onDelete={this.handleDeleteContract}
                onSave={this.handleSave}
                onNew={this.handleCreateNewContract}
              />
          }
          <div className='pipeline-sections'>
            <div className='pipeline-section__input'><Input /></div>
            {
              this.props.contract &&
                <div className='pipeline-section__entityTypes'>
                  <EntityTypes />
                  {fullscreenDiv}
                </div>
            }
            {
              this.props.contract &&
                <div className='pipeline-section__mapping'>
                  <Mapping />
                  {fullscreenDiv}
                </div>
            }
          </div>
          {this.props.contract && <div className='pipeline-output'><Output /></div>}
        </div>
        {this.renderCancelationModal()}
        {this.renderDeletionModal()}
        {this.renderDeleteProgressModal()}
      </div>
    )
  }

  handleCreateNewContract (contract) {
    this.setState({
      newContract: contract
    })
  }

  handleAddNewContract () {
    this.setState({
      isNew: true
    }, () => { this.props.selectSection(CONTRACT_SECTION_SETTINGS) })
  }

  handleCloseSettings () {
    if (this.state.isNew) {
      this.checkUnsavedContract(null)
    } else {
      this.props.selectSection(
        this.state.view === CONTRACT_SECTION_SETTINGS
          ? CONTRACT_SECTION_ENTITY_TYPES
          : this.state.view
      )
    }
  }

  handleDeleteContract () {
    this.setState({
      showDeleteModal: true
    })
  }

  deleteContract (deleteOptions) {
    this.props.deleteContract(this.props.contract.id, deleteOptions)
    this.setState({
      deleteOptions,
      showDeleteModal: false,
      showDeleteProgress: true
    })
  }

  renderCancelationModal () {
    if (!this.state.showCancelModal) {
      return null
    }

    const header = (
      <FormattedMessage
        id='pipeline.new.contract.header'
        defaultMessage='Cancel the new contract?'
      />
    )
    const close = () => { this.setState({ showCancelModal: false }) }
    const buttons = (
      <div>
        <button
          data-qa='pipeline.new.contract.continue'
          className='btn btn-w'
          onClick={close}
        >
          <FormattedMessage
            id='pipeline.new.contract.continue.message'
            defaultMessage='No, Continue Editing'
          />
        </button>

        <button className='btn btn-w btn-primary' onClick={this.handleCancelContract}>
          <FormattedMessage
            id='pipeline.new.contract.cancel'
            defaultMessage='Yes, Cancel'
          />
        </button>
      </div>
    )

    return (
      <Modal
        header={header}
        buttons={buttons}
        onEscape={close}
        onEnter={this.handleCancelContract}
      />
    )
  }

  renderDeletionModal () {
    if (!this.state.showDeleteModal) {
      return null
    }

    return (
      <DeleteModal
        onClose={() => { this.setState({ showDeleteModal: false }) }}
        onDelete={(options) => { this.deleteContract(options) }}
        objectType='contract'
        obj={this.props.contract}
      />
    )
  }

  renderDeleteProgressModal () {
    if (!this.state.showDeleteProgress) {
      return null
    }
    return (
      <DeleteStatus
        header={
          <FormattedMessage
            id='contract.delete.status.header'
            defaultMessage='Deleting contract '
          />
        }
        deleteOptions={this.state.deleteOptions}
        toggle={this.hideModalProgress}
        showModal={this.state.showDeleteProgress}
      />
    )
  }

  hideModalProgress () {
    this.setState({ showDeleteProgress: false })
  }

  handleCancelContract () {
    this.setState({
      newContract: null,
      isNew: false,
      showCancelModal: false
    })
    const nextContract = this.props.pipeline.contracts.length > 0
      ? this.props.pipeline.contracts[0]
      : null

    this.props.selectContract(nextContract)
    this.props.selectSection(nextContract ? this.state.view : PIPELINE_SECTION_INPUT)

    if (this.state.onContractSavedCallback) {
      this.state.onContractSavedCallback()
      this.setState({
        onContractSavedCallback: null
      })
    }
  }

  handleSave (view) {
    this.setState({
      newContract: null,
      isNew: false
    }, () => {
      this.props.selectSection(view || CONTRACT_SECTION_ENTITY_TYPES)
    })
  }

  onContractTabSelected (contract) {
    this.checkUnsavedContract(() => { this.props.selectContract(contract.pipeline, contract.id) })
  }

  toggleSettings () {
    if (this.state.showSettings) {
      this.props.selectSection(CONTRACT_SECTION_ENTITY_TYPES)
    } else if (!this.state.showSettings) {
      this.props.selectSection(CONTRACT_SECTION_SETTINGS)
    }
  }

  renderContractTabs () {
    return this.props.pipeline.contracts.map(contract => (
      <div
        key={contract.id}
        className={`pipeline-tab ${contract.id === this.props.contract.id ? 'active' : ''}`}
        onClick={() => { this.onContractTabSelected(contract) }}
      >
        <span className='contract-name'>{contract.name}</span>

        {
          (contract.mapping_errors || []).length > 0 &&
            <span className={`status ${(contract.mapping_errors || []).length ? 'red' : 'green'}`} />
        }

        <div
          className={`btn-icon settings-button ${this.state.showSettings ? 'active' : ''}`}
          onClick={() => { this.toggleSettings() }}
        >
          <i className='fas fa-wrench' />
        </div>
      </div>
    ))
  }

  renderNewContractTab () {
    const newContract = this.state.newContract
    return newContract && !newContract.created && (
      <div
        key={newContract.id}
        className={`pipeline-tab ${newContract.id === this.props.contract.id ? 'active' : ''}`}
      >
        <span className='contract-name new'>
          <FormattedMessage
            id='pipeline.tab.newContract'
            defaultMessage='new Contract'
          />
        </span>
      </div>
    )
  }

  handleContracts () {
    if (!this.props.pipeline.contracts.length) {
      this.handleAddNewContract()
    } else {
      this.props.selectSection(CONTRACT_SECTION_ENTITY_TYPES)
    }
  }

  handleInput () {
    this.checkUnsavedContract(() => {
      this.props.selectSection(PIPELINE_SECTION_INPUT)
    })
  }

  renderSectionTabs () {
    const { contract = {} } = this.props

    return (
      <div className='pipeline-nav'>
        <div className='pipeline-nav-items'>
          <div
            className='pipeline-nav-item__input'
            onClick={this.handleInput}
          >
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
            onClick={() => { this.props.selectSection(CONTRACT_SECTION_ENTITY_TYPES) }}
          >
            <div className='badge'>
              <i className='fas fa-caret-right' />
            </div>
            <FormattedMessage
              id='pipeline.navbar.entity.types'
              defaultMessage='Entity Types'
            />

          </div>

          <div
            className='pipeline-nav-item__mapping'
            onClick={() => { this.props.selectSection(CONTRACT_SECTION_MAPPING) }}
          >
            <div className='badge'>
              <i className='fas fa-caret-right' />
            </div>
            <FormattedMessage
              id='pipeline.navbar.mapping'
              defaultMessage='Mapping'
            />

          </div>

          <div
            className='pipeline-nav-item__contracts'
            onClick={this.handleContracts}
          >
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
          onClick={() => { this.setState({ showOutput: !this.state.showOutput }) }}
        >
          <div className='badge'>
            <i className='fas fa-caret-right' />
          </div>
          <FormattedMessage
            id='pipeline.navbar.output'
            defaultMessage='Output'
          />
          {
            ((contract && contract.mapping_errors) || []).length > 0 &&
              <span className={`status ${(contract.mapping_errors || []).length ? 'red' : 'green'}`} />
          }
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  loading: pipelines.loading,
  section: pipelines.currentSection,
  pipeline: pipelines.currentPipeline,
  contract: pipelines.currentContract,
  error: pipelines.error,
  deleteStatus: pipelines.deleteStatus
})
const mapDispatchToProps = {
  clearSelection,
  getPipelineById,
  selectContract,
  selectSection,
  deleteContract
}

export default connect(mapStateToProps, mapDispatchToProps)(Pipeline)
