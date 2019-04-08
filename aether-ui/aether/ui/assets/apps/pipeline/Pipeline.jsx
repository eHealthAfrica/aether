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

import { ModalError, NavBar, Modal } from '../components'

import Input from './sections/Input'
import EntityTypes from './sections/EntityTypes'
import Mapping from './sections/Mapping'
import Output from './sections/Output'
import Settings from './sections/Settings'

import {
  clearSelection,
  getPipelineById,
  selectContract,
  selectSection,
  setExitWarning,
  setEditing,
  checkUnsavedContract
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
      view: (view === CONTRACT_SECTION_SETTINGS) ? CONTRACT_SECTION_ENTITY_TYPES : view,
      showSettings: (view === CONTRACT_SECTION_SETTINGS),
      showOutput: false,
      fullscreen: false,
      newContract: null
    }
  }

  componentDidMount () {
    // load current pipeline using location address (router props)
    if (!this.props.isNew) {
      this.props.getPipelineById(this.props.match.params.pid)
    } else {
      this.addNewContract()
    }
  }

  componentDidUpdate (prevProps) {
    if (
      (this.props.contract && (prevProps.section !== this.props.section ||
      (prevProps.contract && prevProps.contract.id !== this.props.contract.id))) &&
      !this.props.isNew
    ) {
      // update router history
      this.props.history.push(`/${this.props.pipeline.id}/${this.props.contract.id}/${this.props.section}`)
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
          view: this.state.view === PIPELINE_SECTION_INPUT ? CONTRACT_SECTION_ENTITY_TYPES : this.state.view,
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

  linksCallBack () {
    this.props.checkUnsavedContract(() => {
      this.props.history.push('/')
      this.props.clearSelection()
    })
  }

  render () {
    const { pipeline } = this.props
    if (!pipeline) {
      return '' // still loading data
    }

    const fullscreenDiv = (
      <div
        className='btn-icon fullscreen-toggle'
        onClick={() => { this.setState({ fullscreen: !this.state.fullscreen }) }}>
        { this.state.fullscreen
          ? <FormattedMessage id='pipeline.navbar.shrink' defaultMessage='fullscreen off' />
          : <FormattedMessage id='pipeline.navbar.fullscreen' defaultMessage='fullscreen on' />
        }
      </div>
    )

    return (
      <div className={`pipelines-container show-pipeline pipeline--${this.state.view}`}>
        { this.props.error && <ModalError error={this.props.error} /> }
        <NavBar showBreadcrumb cb={this.linksCallBack.bind(this)}>
          <div className='breadcrumb-links'>
            <Link onClick={this.linksCallBack.bind(this)}>
              <FormattedMessage
                id='pipeline.navbar.pipelines'
                defaultMessage='Pipelines'
              />
            </Link>
            <span> // </span>
            { pipeline.name }
            { pipeline.isInputReadOnly &&
              <span className='tag'>
                <FormattedMessage
                  id='pipeline.navbar.read-only'
                  defaultMessage='read-only'
                />
              </span>
            }
          </div>
        </NavBar>

        <div className={`
          pipeline
          ${this.state.showOutput ? 'show-output' : ''}
          ${this.state.fullscreen ? 'fullscreen' : ''}
        `}>
          <div className='pipeline-tabs'>
            { this.renderContractTabs() }
            { this.renderNewContractTab() }
            { !this.state.newContract && <button
              type='button'
              className='btn btn-c btn-sm new-contract'
              onClick={this.addNewContract.bind(this)}>
              <span className='details-title'>
                <FormattedMessage
                  id='contract.add.button'
                  defaultMessage='Add contract'
                />
              </span>
            </button>
            }
          </div>

          { this.renderSectionTabs() }

          { this.state.showSettings &&
            <Settings
              onClose={this.onSettingsClosed.bind(this)}
              isNew={this.props.isNew}
              onSave={this.onSave.bind(this)}
              onNew={this.onNewContractCreated.bind(this)}
            />
          }
          <div className='pipeline-sections'>
            <div className='pipeline-section__input'><Input /></div>
            {this.props.contract && <div className='pipeline-section__entityTypes'><EntityTypes />
              { fullscreenDiv }</div>}
            {this.props.contract && <div className='pipeline-section__mapping'><Mapping />
              { fullscreenDiv }</div>}
          </div>
          { this.props.contract && <div className='pipeline-output'><Output /></div> }
        </div>
        { this.renderCancelationModal() }
      </div>
    )
  }

  onNewContractCreated (contract) {
    this.setState({
      newContract: contract
    })
  }

  addNewContract () {
    this.props.setEditing(true)
    this.props.selectSection(CONTRACT_SECTION_SETTINGS)
  }

  onSettingsClosed () {
    if (this.props.isNew) {
      this.props.checkUnsavedContract(() => {})
    } else {
      this.props.selectSection(this.state.view === CONTRACT_SECTION_SETTINGS
        ? CONTRACT_SECTION_ENTITY_TYPES : this.state.view)
      this.props.setExitWarning(false)
    }
  }

  renderCancelationModal () {
    if (!this.props.showCancelModal) {
      return null
    }

    const header = (
      <FormattedMessage
        id='pipeline.new.contract.header'
        defaultMessage='Cancel the new contract?'
      />
    )

    const buttons = (
      <div>
        <button
          data-qa='pipeline.new.contract.continue'
          className='btn btn-w'
          onClick={() => { this.props.setExitWarning(false) }}>
          <FormattedMessage
            id='pipeline.new.contract.continue.message'
            defaultMessage='No, Continue Editing'
          />
        </button>

        <button className='btn btn-w btn-primary' onClick={this.onCancelContract.bind(this, this.props.callback)}>
          <FormattedMessage
            id='pipeline.new.contract.cancel'
            defaultMessage='Yes, Cancel'
          />
        </button>
      </div>
    )

    return (
      <Modal header={header} buttons={buttons} />
    )
  }

  onCancelContract (cb) {
    this.setState({
      newContract: null
    })
    this.props.setExitWarning(false)
    this.props.setEditing(false)
    const nextContract = this.props.pipeline.contracts.length > 0
      ? this.props.pipeline.contracts[0] : null
    this.props.selectContract(nextContract)
    this.props.selectSection(nextContract ? this.state.view : PIPELINE_SECTION_INPUT)
    if (cb) {
      cb()
    }
  }

  onSave (view) {
    this.setState({
      newContract: null
    }, () => {
      this.props.setEditing(false)
      this.props.selectSection(view || CONTRACT_SECTION_ENTITY_TYPES)
    })
  }

  onContractTabSelected (contract) {
    this.props.checkUnsavedContract(() => { this.props.selectContract(contract.pipeline, contract.id) })
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
        onClick={this.onContractTabSelected.bind(this, contract)}>
        <span className='contract-name'>{ contract.name }</span>

        { (contract.mapping_errors || []).length > 0 &&
          <span className={`status ${(contract.mapping_errors || []).length ? 'red' : 'green'}`} />
        }

        <div
          className={`btn-icon settings-button ${this.state.showSettings ? 'active' : ''}`}
          onClick={() => { this.toggleSettings() }}>
          <i className='fas fa-ellipsis-h' />
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

  onContracts () {
    if (!this.props.pipeline.contracts.length) {
      this.addNewContract()
    } else {
      this.props.selectSection(CONTRACT_SECTION_ENTITY_TYPES)
    }
  }

  onInputHandle () {
    this.props.checkUnsavedContract(() => {
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
            onClick={this.onInputHandle.bind(this)}>
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
            onClick={() => { this.props.selectSection(CONTRACT_SECTION_ENTITY_TYPES) }}>
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
            onClick={() => { this.props.selectSection(CONTRACT_SECTION_MAPPING) }}>
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
            onClick={this.onContracts.bind(this)}>
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
          onClick={() => { this.setState({ showOutput: !this.state.showOutput }) }}>
          <div className='badge'>
            <i className='fas fa-caret-right' />
          </div>
          <FormattedMessage
            id='pipeline.navbar.output'
            defaultMessage='Output'
          />
          { ((contract && contract.mapping_errors) || []).length > 0 &&
            <span className={`status ${(contract.mapping_errors || []).length ? 'red' : 'green'}`} />
          }
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  section: pipelines.currentSection,
  pipeline: pipelines.currentPipeline,
  contract: pipelines.currentContract,
  error: pipelines.error,
  showCancelModal: pipelines.exitWarning,
  isNew: pipelines.isEditing,
  callback: pipelines.callback
})
const mapDispatchToProps = {
  clearSelection,
  getPipelineById,
  selectContract,
  selectSection,
  setExitWarning,
  setEditing,
  checkUnsavedContract
}

export default connect(mapStateToProps, mapDispatchToProps)(Pipeline)
