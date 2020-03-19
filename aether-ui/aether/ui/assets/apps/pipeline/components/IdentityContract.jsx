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

export const IdentityContract = ({ contract, inputSchema, setIdentity }) => {
  if (isEmpty(contract) || contract.is_read_only || isEmpty(inputSchema)) {
    return ''
  }

  if (contract.is_identity) {
    return (
      <div className='identity-contract'>
        <h5>
          <FormattedMessage
            id='identity.contract.is.label.info'
            defaultMessage='This is an identity contract'
          />
        </h5>
        <p>
          <FormattedMessage
            id='identity.contract.is.label.message'
            defaultMessage='All Entity Types and Mappings were automatically generated from the input data'
          />
        </p>
      </div>
    )
  }

  const [isIdentity, setIsIdentity] = useState(contract.is_identity || false)
  const [entityTypeName, setEntityTypeName] = useState(inputSchema.name)

  const buildIdentity = (checked) => {
    setIsIdentity(checked)
    if (checked) {
      const mappingRules = deriveMappingRules(inputSchema, entityTypeName)
      const entityTypes = deriveEntityTypes(inputSchema, entityTypeName)

      const identityData = {
        mapping_rules: mappingRules,
        entity_types: entityTypes,
        is_identity: true
      }

      setIdentity(identityData)
    } else {
      setIdentity({})
    }
  }

  return (
    <div className='identity-contract'>
      <div className='toggle-default'>
        <input
          type='checkbox'
          id='toggle'
          checked={isIdentity || false}
          onChange={(event) => { buildIdentity(event.target.checked) }}
        />
        <label htmlFor='toggle' className='title-medium'>
          <FormattedMessage
            id='identity.contract.form.label'
            defaultMessage='Create an identity contract'
          />
        </label>
      </div>
      <p>
        <FormattedMessage
          id='identity.contract.form.label.definition'
          defaultMessage='An identity contract will produce entities
            that are identical with the input. If you choose this setting,
            Aether will generate an Entity Type and a Mapping for you.'
        />
      </p>
      <p>
        <FormattedMessage
          id='identity.contract.form.label.explanation'
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
                id='identity.contract.entity.type.name'
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
  )
}

export const IdentityWarning = ({ show, onCancel, onConfirm }) => {
  if (!show) return ''

  return (
    <Modal
      onEscape={onCancel}
      onEnter={onConfirm}
      header={
        <FormattedMessage
          id='identity.warning.header'
          defaultMessage='Create identity contract'
        />
      }
      buttons={
        <div>
          <button
            id='identity.warning.button.cancel'
            className='btn btn-w'
            onClick={onCancel}
          >
            <FormattedMessage
              id='identity.warning.button.cancel'
              defaultMessage='Cancel'
            />
          </button>
          <button
            data-qa='identity.warning.button.confirm'
            className='btn btn-w btn-primary'
            id='identity.warning.button.yes'
            onClick={onConfirm}
          >
            <FormattedMessage
              id='identity.warning.button.confirm'
              defaultMessage='Yes'
            />
          </button>
        </div>
      }
    >
      <FormattedMessage
        id='identity.warning.content.question'
        defaultMessage='Are you sure that you want to create an identity contract?'
      />
      <FormattedMessage
        id='identity.warning.content.message'
        defaultMessage='This action will overwrite any entity types and mappings that you have created in this contract.'
      />
    </Modal>
  )
}
