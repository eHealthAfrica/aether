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

import { LoadingSpinner, Modal, NavBar } from '../components'

import Input from './sections/Input'
import EntityTypes from './sections/EntityTypes'
import Mapping from './sections/Mapping'
import Output from './sections/Output'
import Settings from './sections/Settings'

import ContractTabs from './components/ContractTabs'

import {
  clearSelection,
  getPipelineById,
  selectContract,
  selectSection,
  startNewContract
} from './redux'

import {
  PIPELINE_SECTION_INPUT,
  CONTRACT_SECTION_ENTITY_TYPES,
  CONTRACT_SECTION_MAPPING
} from '../utils/constants'

class Pipeline extends Component {
  constructor (props) {
    super(props)

    const isNew = props.location.state && props.location.state.isNewContract
    const view = isNew
      ? CONTRACT_SECTION_ENTITY_TYPES
      : props.section || props.match.params.section || PIPELINE_SECTION_INPUT

    this.state = {
      fullscreen: false,
      isNew,
      onContractSavedCallback: null,
      showCancelModal: false,
      showOutput: false,
      showSettings: !!this.props.newContract,
      view
    }
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

      return this.setState({
        view: this.props.section,
        showSettings: this.state.isNew
      })
    }
  }

  checkUnsavedContract (cb) {
    if (this.props.newContract) {
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

    const handleBackToPipelines = () => {
      this.checkUnsavedContract(() => {
        this.props.history.push('/')
        this.props.clearSelection()
      })
    }

    return (
      <div className={`pipelines-container show-pipeline pipeline--${this.state.view}`}>
        <NavBar showBreadcrumb onClick={handleBackToPipelines}>
          <div className='breadcrumb-links'>
            <a onClick={handleBackToPipelines}>
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
          <ContractTabs
            activate={(cId) => {
              this.checkUnsavedContract(() => { this.props.selectContract(pipeline.id, cId) })
            }}
            addNew={() => { this.handleAddNewContract() }}
            showSettings={this.state.showSettings}
            toggleSettings={() => { this.setState({ showSettings: !this.state.showSettings }) }}
          />

          {this.renderSectionTabs()}

          {
            (this.props.newContract || this.props.contract) &&
            this.state.showSettings &&
              <Settings
                onClose={() => {
                  if (this.state.isNew) {
                    this.checkUnsavedContract()
                  } else {
                    this.setState({ showSettings: !this.state.showSettings })
                  }
                }}
                onSave={() => { this.setState({ isNew: false }) }}
              />
          }

          <div className='pipeline-sections'>
            <div className='pipeline-section__input'><Input /></div>
            {
              this.props.contract &&
                <>
                  <div className='pipeline-section__entityTypes'>
                    <EntityTypes />
                    {fullscreenDiv}
                  </div>
                  <div className='pipeline-section__mapping'>
                    <Mapping />
                    {fullscreenDiv}
                  </div>
                </>
            }
          </div>
          {this.props.contract && <div className='pipeline-output'><Output /></div>}
        </div>

        {this.renderCancelationModal()}
      </div>
    )
  }

  handleAddNewContract () {
    this.setState({ isNew: true }, () => { this.props.startNewContract() })
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
    const cancel = () => {
      this.setState({
        isNew: false,
        showCancelModal: false,
        showSettings: false
      })
      const { pipeline, contract } = this.props
      const nextContractId = contract
        ? contract.id
        : pipeline.contracts.length > 0
          ? pipeline.contracts[0].id
          : null

      this.props.selectContract(
        pipeline.id,
        nextContractId,
        nextContractId ? this.state.view : PIPELINE_SECTION_INPUT
      )

      if (this.state.onContractSavedCallback) {
        this.state.onContractSavedCallback()
        this.setState({ onContractSavedCallback: null })
      }
    }

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

        <button className='btn btn-w btn-primary' onClick={cancel}>
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
        onEnter={cancel}
      />
    )
  }

  renderSectionTabs () {
    const { contract = {} } = this.props

    const showInput = () => {
      this.checkUnsavedContract(() => {
        this.props.selectSection(PIPELINE_SECTION_INPUT)
      })
    }
    const showContracts = () => {
      if (!this.props.pipeline.contracts.length) {
        this.handleAddNewContract()
      } else {
        this.props.selectSection(CONTRACT_SECTION_ENTITY_TYPES)
      }
    }

    return (
      <div className='pipeline-nav'>
        <div className='pipeline-nav-items'>
          <div
            className='pipeline-nav-item__input'
            onClick={showInput}
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
            className='pipeline-nav-item__contracts'
            onClick={showContracts}
          >
            <div className='badge'>
              <i className='fas fa-caret-right' />
            </div>
            <FormattedMessage
              id='pipeline.navbar.contracts'
              defaultMessage='Contracts'
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
  contract: pipelines.currentContract,
  newContract: pipelines.newContract,
  pipeline: pipelines.currentPipeline,
  section: pipelines.currentSection
})

const mapDispatchToProps = {
  clearSelection,
  getPipelineById,
  selectContract,
  selectSection,
  startNewContract
}

export default connect(mapStateToProps, mapDispatchToProps)(Pipeline)
