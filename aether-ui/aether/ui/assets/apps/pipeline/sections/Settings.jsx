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

import React, { useState, useEffect } from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { addContract, updateContract } from '../redux'

import ContractPublishButton from '../components/ContractPublishButton'
import ContractRemoveButton from '../components/ContractRemoveButton'
import IdentityContract from '../components/IdentityContract'
import SubmissionCard from '../components/SubmissionCard'

const Settings = ({
  addContract,
  contract,
  inputData,
  inputSchema,
  mappingset,
  onClose,
  onSave,
  updateContract
}) => {
  const [prevContract, setPrevContract] = useState(contract)
  const [contractName, setContractName] = useState(contract.name)
  const [showIdentityWarning, setShowIdentityWarning] = useState(false)

  useEffect(() => {
    if (prevContract !== contract) {
      setPrevContract(contract)
      setContractName(contract.name)
    }
  })

  const handlePreSave = (contract) => {
    if (contract.is_identity) {
      setShowIdentityWarning(true)
    } else {
      handleSave({ ...contract, name: contractName })
    }
  }

  const handleSave = (contract) => {
    setShowIdentityWarning(false)
    if (!contract.created) {
      addContract({ ...contract, name: contractName })
      onSave()
    } else {
      updateContract({ ...contract, name: contractName })
      onClose()
    }
  }

  return (
    <div className='pipeline-settings'>
      <div className='contract-form'>
        <div className='form-group'>
          <label className='form-label'>
            <FormattedMessage
              id='settings.contract.name'
              defaultMessage='Contract name'
            />
          </label>
          <input
            type='text'
            required
            name='name'
            className='input-d input-large'
            value={contractName || ''}
            onChange={(e) => { setContractName(e.target.value) }}
            disabled={contract.is_read_only}
          />
        </div>

        <IdentityContract
          key={contract.id}
          contract={contract}
          inputSchema={inputSchema}
          showWarning={showIdentityWarning}
          onGenerate={handleSave}
          onCancel={() => { setShowIdentityWarning(false) }}
        />

        <div className='settings-section'>
          <div>
            <ContractPublishButton
              contract={contract}
              className='btn btn-d btn-publish'
            />
          </div>

          {
            contract.published_on &&
              <div className='mt-4'>
                <SubmissionCard
                  mappingset={mappingset}
                  inputData={inputData}
                />
              </div>
          }
        </div>
        <div className='settings-actions'>
          <button
            onClick={() => { onClose() }}
            type='button'
            className='btn btn-d btn-big'
            id='pipeline.settings.cancel.button'
          >
            <span className='details-title'>
              <FormattedMessage
                id='settings.button.cancel'
                defaultMessage='Cancel'
              />
            </span>
          </button>
          {
            !contract.is_read_only &&
              <button
                id='settings-contract-save'
                className='btn btn-d btn-primary btn-big ml-4'
                onClick={() => { handlePreSave(contract) }}
              >
                <span className='details-title'>
                  <FormattedMessage
                    id='settings.contract.save'
                    defaultMessage='Save'
                  />
                </span>
              </button>
          }

          <ContractRemoveButton />
        </div>
      </div>
    </div>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  mappingset: pipelines.currentPipeline && pipelines.currentPipeline.mappingset,
  inputData: pipelines.currentPipeline && pipelines.currentPipeline.input,
  inputSchema: pipelines.currentPipeline && pipelines.currentPipeline.schema,

  contract: pipelines.newContract || pipelines.currentContract,
  pipeline: pipelines.currentPipeline
})
const mapDispatchToProps = { addContract, updateContract }

export default connect(mapStateToProps, mapDispatchToProps)(Settings)
