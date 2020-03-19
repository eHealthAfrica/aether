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
import { isEmpty } from '../../utils'
import { deriveEntityTypes, deriveMappingRules } from '../../utils/avro-utils'

import { Modal } from '../../components'
import ContractPublishButton from '../components/ContractPublishButton'
import SubmissionCard from '../components/SubmissionCard'

const IdentityContract = ({
  contract,
  inputSchema,
  showWarning,
  onGenerate,
  onCancel
}) => {
  if (contract.is_read_only || isEmpty(inputSchema)) {
    return ''
  }

  const [isIdentity, setIsIdentity] = useState(contract.is_identity)
  const [entityTypeName, setEntityTypeName] = useState(inputSchema.name)

  const handleGenerate = () => {
    const mappingRules = deriveMappingRules(inputSchema, entityTypeName)
    const entityTypes = deriveEntityTypes(inputSchema, entityTypeName)

    const updatedContract = {
      ...contract,
      mapping_rules: mappingRules,
      entity_types: entityTypes,
      is_identity: true
    }

    onGenerate(updatedContract)
  }

  return (
    <>
      {
        !contract.is_identity &&
          <div className='identity-contract'>
            <div className='toggle-default'>
              <input
                type='checkbox'
                id='toggle'
                checked={isIdentity}
                onChange={(event) => { setIsIdentity(event.target.checked) }}
              />
              <label
                htmlFor='toggle'
                className='title-medium'
              >
                <FormattedMessage
                  id='settings.identity.unchecked.help-1'
                  defaultMessage='Create an identity contract'
                />
              </label>
            </div>
            <p>
              <FormattedMessage
                id='settings.identity.unchecked.help-2'
                defaultMessage='An identity contract will produce entities
                  that are identical with the input. If you choose this setting,
                  Aether will generate an Entity Type and Mapping for you.'
              />
            </p>
            <p>
              <FormattedMessage
                id='settings.identity.unchecked.help-3'
                defaultMessage="This can be useful in situations where you
                  want to make use of Aether's functionality without transforming
                  the data. Alternatively, you can use the generate Entity Type
                  and Mapping as a starting point for a more complex contract."
              />
            </p>
            {
              isIdentity &&
                <div className='form-group'>
                  <label className='form-label'>
                    <FormattedMessage
                      id='settings.contract.identity.name'
                      defaultMessage='Entity Type name'
                    />
                  </label>
                  <input
                    type='text'
                    required
                    name='name'
                    className='input-d input-large'
                    value={entityTypeName || ''}
                    onChange={(e) => { setEntityTypeName(e.target.value) }}
                  />
                </div>
            }
          </div>
      }

      {
        contract.is_identity &&
          <div className='identity-contract'>
            <h5>
              <FormattedMessage
                id='settings.identity.checked.help-1'
                defaultMessage='This is an identity contract'
              />
            </h5>
            <p>
              <FormattedMessage
                id='settings.identity.checked.help-2'
                defaultMessage='All Entity Types and Mappings were automatically generated from the input data'
              />
            </p>
          </div>
      }

      {
        showWarning &&
          <Modal
            onEscape={onCancel}
            onEnter={handleGenerate}
            header={
              <FormattedMessage
                id='settings.identity.header'
                defaultMessage='Create identity contract'
              />
            }
            buttons={
              <div>
                <button
                  id='settings.identity.modal.cancel'
                  className='btn btn-w'
                  onClick={onCancel}
                >
                  <FormattedMessage
                    id='settings.identity.button.cancel'
                    defaultMessage='Cancel'
                  />
                </button>
                <button
                  data-qa='contract.identity.button.confirm'
                  className='btn btn-w btn-primary'
                  id='settings.identity.modal.yes'
                  onClick={handleGenerate}
                >
                  <FormattedMessage
                    id='settings.identity.button.confirm'
                    defaultMessage='Yes'
                  />
                </button>
              </div>
            }
          >
            <FormattedMessage
              id='settings.identity.content.question'
              defaultMessage='Are you sure that you want to create an identity contract?'
            />
            <FormattedMessage
              id='settings.identity.content.warning'
              defaultMessage='This action will overwrite any entity types and mappings that you have created in this contract.'
            />
          </Modal>
      }
    </>
  )
}

const Settings = ({
  addContract,
  contract,
  inputData,
  inputSchema,
  mappingset,
  onClose,
  onDelete,
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
          {
            !contract.is_read_only && contract.created &&
              <button
                className='btn btn-d btn-red btn-big'
                onClick={() => { onDelete() }}
              >
                <span className='details-title'>
                  <FormattedMessage
                    id='settings.contract.delete'
                    defaultMessage='Delete Contract'
                  />
                </span>
              </button>
          }
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
