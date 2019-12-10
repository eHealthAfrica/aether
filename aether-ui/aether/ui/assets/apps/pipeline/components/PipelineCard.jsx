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

import PipelineInfo from './PipelineInfo'
import ContractCard from './ContractCard'
import PipelineRename from './PipelineRename'
import PipelineActions from './PipelineActions'

import { selectPipeline, renamePipeline } from '../redux'

class PipelineCard extends Component {
  constructor (props) {
    super(props)

    this.state = { isRenaming: false, showInfo: false }
  }

  render () {
    const { pipeline, history } = this.props
    const { isRenaming, showInfo } = this.state
    const { id, name, isInputReadOnly, mappingset, contracts } = pipeline

    const handleRenameSave = (newName) => {
      this.props.renamePipeline(id, newName)
      this.setState({ isRenaming: false })
    }

    const handlePipelineSelect = () => {
      this.props.selectPipeline(id)
      history.push(`/${id}/`)
    }

    const setShowInfo = (event, showInfo) => {
      event.stopPropagation()
      this.setState({ showInfo })
    }

    return (
      <div className='pipeline-preview'>
        <div className='preview-heading'>
          <span className='pipeline-name'>// {name}</span>
          {
            isRenaming
              ? (
                <PipelineRename
                  name={name}
                  onCancel={() => { this.setState({ isRenaming: false }) }}
                  onSave={handleRenameSave}
                />
              )
              : (
                <PipelineActions
                  delete={this.props.delete}
                  rename={() => { this.setState({ isRenaming: true }) }}
                  pipeline={pipeline}
                  history={history}
                />
              )
          }
        </div>

        <div
          className={`preview-input ${isInputReadOnly ? 'pipeline-readonly' : ''}`}
          onClick={handlePipelineSelect}
        >
          {
            isInputReadOnly &&
              <span className='tag'>
                <FormattedMessage
                  id='pipeline.card.read-only'
                  defaultMessage='read-only'
                />
              </span>
          }

          <div className='input-heading'>
            <span className='badge badge-circle badge-c'>
              <i className='fas fa-file' />
            </span>
            <span className='input-name'>
              {name} {mappingset && (
                <i
                  className='ml-1 fas fa-info-circle published-info-icon'
                  onClick={(event) => { setShowInfo(event, true) }}
                />
              )}
            </span>
          </div>
        </div>

        <div className='preview-contracts'>
          {
            contracts.map(contract => (
              <ContractCard
                key={contract.id}
                contract={contract}
                history={history}
              />
            ))
          }
        </div>

        {mappingset && (
          <PipelineInfo
            pipeline={pipeline}
            showInfo={showInfo}
            setShowInfo={setShowInfo}
          />
        )}
      </div>
    )
  }
}

const mapStateToProps = () => ({})
const mapDispatchToProps = { selectPipeline, renamePipeline }

export default connect(mapStateToProps, mapDispatchToProps)(PipelineCard)
