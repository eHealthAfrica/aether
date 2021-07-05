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

import React, { useState } from 'react'
import { useHistory } from 'react-router-dom'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import PipelineInfo from './PipelineInfo'
import ContractCard from './ContractCard'
import PipelineActions from './PipelineActions'

import { selectPipeline } from '../redux'

const PipelineCard = ({ pipeline, selectPipeline }) => {
  const history = useHistory()
  const [showInfo, setShowInfo] = useState(false)

  const { id, name, isInputReadOnly, mappingset, contracts } = pipeline

  const handlePipelineSelect = () => {
    selectPipeline(id)
    history.push(`/${id}/`)
  }

  return (
    <div className='pipeline-preview'>
      <div className='preview-heading'>
        <span className='pipeline-name'>&#47;&#47; {name}</span>

        <PipelineActions pipeline={pipeline} />
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
                className='ms-1 fas fa-info-circle published-info-icon'
                onClick={(event) => {
                  event.stopPropagation()
                  setShowInfo(true)
                }}
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
            />
          ))
        }
      </div>

      {
        mappingset && showInfo &&
          <PipelineInfo
            pipeline={pipeline}
            close={(event) => {
              event && event.stopPropagation()
              setShowInfo(false)
            }}
          />
      }
    </div>
  )
}

const mapStateToProps = () => ({})
const mapDispatchToProps = { selectPipeline }

export default connect(mapStateToProps, mapDispatchToProps)(PipelineCard)
