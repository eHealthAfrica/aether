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
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'
import { Modal } from '../../components'

const MESSAGES = defineMessages({
  title: {
    defaultMessage: 'Rename pipeline {name}',
    id: 'rename.modal.header'
  },
  namePlaceholder: {
    defaultMessage: 'Name of pipeline',
    id: 'rename.modal.name.placeholder'
  }
})

const RenameForm = ({ initialValue, placeholder, onSave, onCancel }) => {
  const [value, setValue] = useState(initialValue)

  return (
    <form>
      <div className='form-group'>
        <label className='form-label'>
          <FormattedMessage
            id='rename.modal.name.label'
            defaultMessage='Pipeline name'
          />
        </label>
        <input
          type='text'
          required
          className='text-input input-large'
          placeholder={placeholder}
          value={value}
          onChange={(event) => { setValue(event.target.value) }}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              onSave(event.target.value)
            }
          }}
        />
      </div>

      <div className='modal-actions'>
        <button
          data-qa='rename.modal.button.cancel'
          className='btn btn-w'
          onClick={onCancel}
        >
          <FormattedMessage
            id='rename.modal.button.cancel'
            defaultMessage='Cancel'
          />
        </button>
        <button
          role='button'
          className='btn btn-w btn-primary'
          onClick={() => { onSave(value) }}
        >
          <FormattedMessage
            id='rename.modal.button.save'
            defaultMessage='Save'
          />
        </button>
      </div>
    </form>
  )
}

const PipelineRename = ({
  name,
  onCancel,
  onSave,
  intl: { formatMessage }
}) => (
  <Modal
    onEscape={onCancel}
    header={formatMessage(MESSAGES.title, { name: <b>{name}</b> })}
  >
    <RenameForm
      initialValue={name}
      placeholder={formatMessage(MESSAGES.namePlaceholder)}
      onSave={onSave}
      onCancel={onCancel}
    />
  </Modal>
)

export default injectIntl(PipelineRename)
