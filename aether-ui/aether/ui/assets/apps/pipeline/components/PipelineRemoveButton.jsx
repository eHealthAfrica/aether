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

import React, { useState } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'

import { deletePipeline } from '../redux'

import DeleteStatus from './DeleteStatus'
import DeleteModal from './DeleteModal'

const PipelineRemoveButton = ({ pipeline, deletePipeline }) => {
  const [optionsRemove, setOptionsRemove] = useState({})
  const [showRemoveModal, setShowRemoveModal] = useState(false)
  const [showRemoveProgress, setShowRemoveProgress] = useState(false)

  return (
    <>
      <li onClick={() => { setShowRemoveModal(true) }}>
        <FormattedMessage
          id='pipeline.option.remove'
          defaultMessage='Remove Pipeline'
        />
      </li>

      {
        showRemoveModal &&
          <DeleteModal
            onClose={() => { setShowRemoveModal(false) }}
            onDelete={(deleteOptions) => {
              setOptionsRemove(deleteOptions)
              setShowRemoveModal(false)
              setShowRemoveProgress(true)
              deletePipeline(pipeline.id, deleteOptions)
            }}
            objectType='pipeline'
            obj={pipeline}
          />
      }
      {
        showRemoveProgress &&
          <DeleteStatus
            header={
              <FormattedMessage
                id='pipeline.list.delete.status.header'
                defaultMessage='Deleting pipeline'
              />
            }
            deleteOptions={optionsRemove}
            toggle={() => { setShowRemoveProgress(false) }}
            showModal={showRemoveProgress}
          />
      }
    </>
  )
}

const mapStateToProps = () => ({})
const mapDispatchToProps = { deletePipeline }

export default connect(mapStateToProps, mapDispatchToProps)(PipelineRemoveButton)
