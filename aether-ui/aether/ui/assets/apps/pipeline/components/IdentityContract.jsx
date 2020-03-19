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
import { FormattedMessage } from 'react-intl'

import { isEmpty } from '../../utils'
import { deriveEntityTypes, deriveMappingRules } from '../../utils/avro-utils'

import { Modal } from '../../components'

const IdentityContract = ({
  contract,
  inputSchema,
  showWarning,
  onGenerate,
  onCancel
}) => {
  if (isEmpty(contract) || contract.is_read_only || isEmpty(inputSchema)) {
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

export default IdentityContract
