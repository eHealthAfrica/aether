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

import React from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import ContractPublishButton from './ContractPublishButton'

import { selectContract, selectSection } from '../redux'
import { CONTRACT_SECTION_ENTITY_TYPES } from '../../utils/constants'

const ContractCard = ({
  contract,
  selectContract,
  selectSection,
  history
}) => {
  const handleSelectContract = (pipelineId, contractId) => {
    selectContract(pipelineId, contractId)
    selectSection(CONTRACT_SECTION_ENTITY_TYPES)
    history.push(`/${pipelineId}/${contractId}/${CONTRACT_SECTION_ENTITY_TYPES}`)
  }

  return (
    <div
      key={contract.id}
      className={`preview-contract ${contract.is_read_only ? 'pipeline-readonly' : ''}`}
      onClick={() => { handleSelectContract(contract.pipeline, contract.id) }}
    >
      {
        contract.is_read_only &&
          <span className='tag'>
            <FormattedMessage
              id='contract.card.read-only'
              defaultMessage='read-only'
            />
          </span>
      }

      <div className='contract-heading'>
        <h2 className='contract-name'>{contract.name}</h2>

        <div className='contract-summaries'>
          <div className='summary-entity-types'>
            <span className='badge badge-c badge-big'>
              {(contract.entity_types || []).length}
            </span>
            <FormattedMessage
              id='contract.card.entity.types'
              defaultMessage='Entity-Types'
            />
          </div>

          <div className='summary-errors'>
            <span
              className={`
                badge badge-c badge-big
                ${(contract.mapping_errors || []).length ? 'error' : ''}
              `}
            >
              {(contract.mapping_errors || []).length}
            </span>
            <FormattedMessage
              id='contract.card.errors'
              defaultMessage='Errors'
            />
          </div>
        </div>
      </div>

      <div className='contract-publish'>
        <ContractPublishButton
          contract={contract}
          className='btn btn-d btn-publish'
        />
      </div>
    </div>
  )
}

const mapStateToProps = () => ({})
const mapDispatchToProps = { selectContract, selectSection }

export default connect(mapStateToProps, mapDispatchToProps)(ContractCard)
