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
import { FormattedMessage, injectIntl, defineMessages } from 'react-intl'
import { Modal } from '../../components'

const MESSAGES = defineMessages({
  pipeline: {
    id: 'modal.delete.object.type.pipeline',
    defaultMessage: 'pipeline'
  },
  contract: {
    id: 'modal.delete.object.type.contract',
    defaultMessage: 'contract'
  }
})

const DeleteModal = ({
  onClose,
  onDelete,
  obj,
  objectType,
  intl: { formatMessage }
}) => {
  const [schemas, setSchemas] = useState(false)
  const [entities, setEntities] = useState(false)
  const [submissions, setSubmissions] = useState(false)

  const objType = formatMessage(MESSAGES[objectType || 'pipeline'])
  const header = (
    <span>
      <FormattedMessage
        id='modal.delete.text'
        defaultMessage='Delete {objType} {objName}'
        values={{ objType, objName: <b>{obj.name}</b> }}
      />
    </span>
  )
  const remove = () => { onDelete({ schemas, submissions, entities }) }

  const buttons = (
    <div>
      <button
        data-qa='delete.modal.button.cancel'
        className='btn btn-w'
        onClick={onClose}
      >
        <FormattedMessage
          id='delete.modal.button.cancel'
          defaultMessage='Cancel'
        />
      </button>

      <button
        className='btn btn-w btn-primary'
        onClick={remove}
      >
        <FormattedMessage
          id='delete.modal.button.delete'
          defaultMessage='Delete'
        />
      </button>
    </div>
  )

  return (
    <Modal
      header={header}
      buttons={buttons}
      onEnter={remove}
      onEscape={onClose}
    >
      <label className='title-medium mt-4'>
        <FormattedMessage
          id='delete.modal.message-2'
          defaultMessage='Would you also like to delete any of the following?'
        />
      </label>
      {
        objectType === 'pipeline' &&
          <div className='check-default ml-4'>
            <input
              type='checkbox'
              id='check1'
              checked={submissions}
              onChange={(e) => {
                setSubmissions(e.target.checked)
              }}
            />
            <label htmlFor='check1'>
              <FormattedMessage
                id='modal.delete.submissions.text'
                defaultMessage='Data <b>submitted to</b> this pipeline (Submissions)'
                values={{ b: text => <b>{text}</b> }}
              />
            </label>
          </div>
      }
      <div className='check-default ml-4'>
        <input
          type='checkbox'
          id='check2'
          checked={schemas}
          onChange={(e) => {
            setEntities(e.target.checked)
            setSchemas(e.target.checked)
          }}
        />
        <label htmlFor='check2'>
          <FormattedMessage
            id='delete.modal.all.entity-types-0'
            defaultMessage='Entity Types (Schemas)'
          />
        </label>
      </div>
      <div className='check-default ml-4 check-indent'>
        <input
          type='checkbox'
          id='check3'
          checked={entities}
          onChange={(e) => {
            if (!e.target.checked) {
              setEntities(e.target.checked)
              setSchemas(e.target.checked)
            } else {
              setEntities(e.target.checked)
            }
          }}
        />
        <label htmlFor='check3'>
          <FormattedMessage
            id='modal.delete.entities.text'
            defaultMessage='Data <b>created by</b> this {objType} (Entities)'
            values={{ b: text => <b>{text}</b>, objType }}
          />
        </label>
      </div>
    </Modal>
  )
}

export default injectIntl(DeleteModal)
