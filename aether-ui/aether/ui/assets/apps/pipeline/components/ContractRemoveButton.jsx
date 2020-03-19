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
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { deleteContract } from '../redux'

import DeleteModal from '../components/DeleteModal'
import DeleteStatus from '../components/DeleteStatus'

const ContractRemoveButton = ({ contract, deleteContract }) => {
  if (!contract || contract.is_read_only) {
    return ''
  }

  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showDeleteProgress, setShowDeleteProgress] = useState(false)
  const [deleteOptions, setDeleteOptions] = useState()

  const handleDelete = (options) => {
    deleteContract(contract.id, deleteOptions)
    setDeleteOptions(options)
    setShowDeleteModal(false)
    setShowDeleteProgress(true)
  }

  return (
    <>
      <button
        className='btn btn-d btn-red btn-big'
        onClick={() => { setShowDeleteModal(true) }}
      >
        <span className='details-title'>
          <FormattedMessage
            id='contract.remove.title'
            defaultMessage='Delete Contract'
          />
        </span>
      </button>

      {
        showDeleteModal &&
          <DeleteModal
            onClose={() => { setShowDeleteModal(false) }}
            onDelete={(options) => { handleDelete(options) }}
            objectType='contract'
            obj={contract}
          />
      }

      {
        showDeleteProgress &&
          <DeleteStatus
            header={
              <FormattedMessage
                id='contract.remove.status.header'
                defaultMessage='Deleting contract '
              />
            }
            deleteOptions={deleteOptions}
            toggle={() => { setShowDeleteProgress(false) }}
            showModal={showDeleteProgress}
          />
      }
    </>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  contract: pipelines.currentContract
})
const mapDispatchToProps = { deleteContract }

export default connect(mapStateToProps, mapDispatchToProps)(ContractRemoveButton)
