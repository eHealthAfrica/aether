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

import { ModalError, NavBar } from '../components'

import ContractAddButton from './components/ContractAddButton'
import Input from './sections/Input'
import EntityTypes from './sections/EntityTypes'
import Mapping from './sections/Mapping'
import Output from './sections/Output'
import Settings from './sections/Settings'

import { clearSelection, getPipelineById, selectContract, selectSection } from './redux'

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
      fullscreen: false
    }

    // load current pipeline using location address (router props)
    props.getPipelineById(props.match.params.pid)
  }

  componentDidUpdate (prevProps) {
    if (
      prevProps.section !== this.props.section ||
      (prevProps.contract && this.props.contract && prevProps.contract.id !== this.props.contract.id)
    ) {
      // update router history
      this.props.history.push(`/${this.props.pipeline.id}/${this.props.contract.id}/${this.props.section}`)
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

  render () {
    const { pipeline } = this.props
    if (!pipeline) {
      return '' // still loading data
    }

    return (
      <div className={`pipelines-container show-pipeline pipeline--${this.state.view}`}>
        { this.props.error && <ModalError error={this.props.error} /> }
        <NavBar showBreadcrumb>
          <div className='breadcrumb-links'>
            <Link to='/' onClick={() => { this.props.clearSelection() }}>
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
            <ContractAddButton
              className='btn btn-c btn-sm new-contract'
              pipeline={pipeline}
            />
          </div>

          { this.renderSectionTabs() }

          { this.state.showSettings &&
            <Settings onClose={() => { this.props.selectSection(this.state.view) }} />
          }
          <div className='pipeline-sections'>
            <div className='pipeline-section__input'><Input /></div>
            <div className='pipeline-section__entityTypes'><EntityTypes /></div>
            <div className='pipeline-section__mapping'><Mapping /></div>
          </div>
          <div className='pipeline-output'><Output /></div>
        </div>
      </div>
    )
  }

  renderContractTabs () {
    return this.props.pipeline.contracts.map(contract => (
      <div
        key={contract.id}
        className={`pipeline-tab ${contract.id === this.props.contract.id ? 'active' : ''}`}
        onClick={() => { this.props.selectContract(contract.pipeline, contract.id) }}>
        <span className='contract-name'>{ contract.name }</span>

        { (contract.mapping_errors || []).length > 0 &&
          <span className={`status ${(contract.mapping_errors || []).length ? 'red' : 'green'}`} />
        }

        <div
          className={`btn-icon settings-button ${this.state.showSettings ? 'active' : ''}`}
          onClick={() => { this.props.selectSection(CONTRACT_SECTION_SETTINGS) }}>
          <i className='fas fa-ellipsis-h' />
        </div>
      </div>
    ))
  }

  renderSectionTabs () {
    const { contract } = this.props

    const fullscreenDiv = (
      <div
        className='btn-icon fullscreen-toggle'
        onClick={() => { this.setState({ fullscreen: !this.state.fullscreen }) }}>
        { this.state.fullscreen
          ? <FormattedMessage id='pipeline.navbar.shrink' defaultMessage='shrink' />
          : <FormattedMessage id='pipeline.navbar.fullscreen' defaultMessage='fullscreen' />
        }
      </div>
    )

    return (
      <div className='pipeline-nav'>
        <div className='pipeline-nav-items'>
          <div
            className='pipeline-nav-item__input'
            onClick={() => { this.props.selectSection(PIPELINE_SECTION_INPUT) }}>
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
            { fullscreenDiv }
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
            { fullscreenDiv }
          </div>

          <div
            className='pipeline-nav-item__contracts'
            onClick={() => { this.props.selectSection(CONTRACT_SECTION_ENTITY_TYPES) }}>
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
          { (contract.mapping_errors || []).length > 0 &&
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
  error: pipelines.error
})
const mapDispatchToProps = {
  clearSelection,
  getPipelineById,
  selectContract,
  selectSection
}

export default connect(mapStateToProps, mapDispatchToProps)(Pipeline)
