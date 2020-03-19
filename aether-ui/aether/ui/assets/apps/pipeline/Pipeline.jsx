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

import Sections from './sections/Sections'
import Settings from './sections/Settings'
import ContractTabs from './components/ContractTabs'

import { clearSelection, getPipelineById, selectContract } from './redux'
import { PIPELINE_SECTION_INPUT } from '../utils/constants'

class Pipeline extends Component {
  constructor (props) {
    super(props)

    this.state = {
      fullscreen: false,
      onContractSavedCallback: null,
      showCancelModal: false,
      showOutput: false,
      showSettings: !!this.props.newContract
    }
  }

  componentDidMount () {
    // load current pipeline using location address (router props)
    this.props.getPipelineById(this.props.match.params.pid)
  }

  componentDidUpdate (prevProps) {
    if (
      !this.props.newContract &&
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
          showSettings: false,
          showOutput: false,
          fullscreen: false
        })
      }

      return this.setState({
        showSettings: !!this.props.newContract
      })
    }
  }

  render () {
    const { pipeline } = this.props
    if (!pipeline) {
      return <LoadingSpinner /> // still loading data
    }

    const checkUnsavedContract = (cb) => {
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

    const handleBackToPipelines = () => {
      checkUnsavedContract(() => {
        this.props.history.push('/')
        this.props.clearSelection()
      })
    }

    return (
      <div className={`pipelines-container show-pipeline pipeline--${this.props.section}`}>
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
            checkUnsavedContract={checkUnsavedContract.bind(this)}
            showSettings={this.state.showSettings}
            toggleSettings={() => { this.setState({ showSettings: !this.state.showSettings }) }}
          />

          <Sections
            addNewContract={() => { this.setState({ showSettings: true }) }}
            checkUnsavedContract={checkUnsavedContract.bind(this)}
            fullscreen={this.state.fullscreen}
            toggleFullscreen={() => { this.setState({ fullscreen: !this.state.fullscreen }) }}
            toggleOutput={() => { this.setState({ showOutput: !this.state.showOutput }) }}
          />

          {
            (this.props.newContract || this.state.showSettings) &&
              <Settings
                onClose={() => {
                  if (this.props.newContract) {
                    checkUnsavedContract()
                  } else {
                    this.setState({ showSettings: false })
                  }
                }}
                onSave={() => { this.setState({ showSettings: false }) }}
              />
          }
          {this.renderCancelationModal()}
        </div>
      </div>
    )
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
        nextContractId ? this.props.section : PIPELINE_SECTION_INPUT
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
  selectContract
}

export default connect(mapStateToProps, mapDispatchToProps)(Pipeline)
