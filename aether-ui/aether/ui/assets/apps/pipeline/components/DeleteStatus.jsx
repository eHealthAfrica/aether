/*
 * Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import React, { useEffect } from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { Modal } from '../../components'

const DeleteStatus = ({
  deleteOptions,
  deleteStatus,
  error,
  header,
  showModal,
  toggle
}) => {
  useEffect(() => {
    if (error || (deleteStatus && deleteStatus.not_published)) {
      toggle()
    }
  })

  if (!showModal) {
    return ''
  }

  const close = () => { toggle() }
  const buttons = !deleteStatus
    ? ''
    : (
      <div className='modal-actions'>
        <button className='btn btn-primary btn-w' onClick={close}>
          <FormattedMessage
            id='delete.progress.modal.ok'
            defaultMessage='Close'
          />
        </button>
      </div>
      )

  return (
    <Modal
      buttons={buttons}
      header={header}
      onEnter={close}
      onEscape={close}
    >
      {
        !deleteStatus && (
          <label className='title-medium mt-4'>
            <FormattedMessage
              id='delete.modal.status.head-1'
              defaultMessage='Deleting kernel artefacts...'
            />
            <i className='ms-5 fas fa-cog fa-spin' />
          </label>
        )
      }

      {
        deleteOptions.entities &&
        deleteStatus &&
        Object.prototype.hasOwnProperty.call(deleteStatus, 'entities') &&
          <div>
            <label className='form-label'>
              <span className='badge badge-b'>
                {deleteStatus.entities.total}
              </span>
              <FormattedMessage
                id='delete.modal.entities.status'
                defaultMessage='Entities deleted'
              />
            </label>
            <div className='ms-5'>
              {
                deleteStatus.entities.schemas.map(schema => (
                  <div key={schema.name}>
                    <i className='fas fa-check me-2' />
                    <label>
                      {schema.name} : {schema.count}
                    </label>
                  </div>
                ))
              }
            </div>
          </div>
      }

      {
        deleteOptions.schemas &&
        deleteStatus &&
        deleteStatus.schemas &&
          <div>
            <label className='form-label mt-4'>
              <span className='badge badge-b'>
                {Object.keys(deleteStatus.schemas).length}
              </span>
              <FormattedMessage
                id='delete.modal.entity.types.status'
                defaultMessage='Entity types deleted'
              />
            </label>
            <div className='ms-5'>
              {
                Object.keys(deleteStatus.schemas).map(schema => (
                  <div key={schema}>
                    <i className='fas fa-check me-2' />
                    <label>
                      {schema} :
                      {
                        deleteStatus.schemas[schema].is_deleted
                          ? (
                            <FormattedMessage
                              id='delete.modal.entity.types.status.deleted'
                              defaultMessage='Deleted'
                            />)
                          : (
                            <FormattedMessage
                              id='delete.modal.entity.types.status.not.deleted'
                              defaultMessage='Not deleted, used by other mappings'
                            />)
                      }
                    </label>
                  </div>
                ))
              }
            </div>

            {
              Object.keys(deleteStatus.schemas).length === 0 &&
                <label>
                  <FormattedMessage
                    id='delete.modal.entity.types.empty'
                    defaultMessage='No entity types to delete'
                  />
                </label>
            }
          </div>
      }

      {
        deleteOptions.submissions &&
        deleteStatus &&
        Object.prototype.hasOwnProperty.call(deleteStatus, 'submissions') &&
          <div>
            <label className='form-label mt-4'>
              <span className='badge badge-b'>{deleteStatus.submissions}</span>
              <FormattedMessage
                id='delete.modal.submissions.status'
                defaultMessage='Submissions deleted'
              />
            </label>
          </div>
      }
    </Modal>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  error: pipelines.error,
  deleteStatus: pipelines.deleteStatus
})

export default connect(mapStateToProps, {})(DeleteStatus)
