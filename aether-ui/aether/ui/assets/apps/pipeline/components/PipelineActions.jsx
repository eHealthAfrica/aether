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
import OutsideClickHandler from 'react-outside-click-handler'

import PipelineRemoveButton from './PipelineRemoveButton'
import PipelineRenameButton from './PipelineRenameButton'
import ContractAddButton from './ContractAddButton'

const PipelineOptions = ({ pipeline }) => {
  const [showOptions, setShowOptions] = useState(false)

  return (
    <OutsideClickHandler onOutsideClick={() => { setShowOptions(false) }}>
      <>
        <button
          type='button'
          className='btn btn-c btn-square me-2'
          onClick={() => { setShowOptions(!showOptions) }}
        >
          <span className='details-title'>
            <i className='fas fa-ellipsis-h' />
          </span>
        </button>

        <ul className={`options ${showOptions ? '' : 'd-none'}`}>
          <PipelineRemoveButton pipeline={pipeline} />
          <PipelineRenameButton pipeline={pipeline} />
        </ul>
      </>
    </OutsideClickHandler>
  )
}

const PipelineActions = ({ pipeline }) => {
  return (
    <div className='pipeline-actions'>
      <PipelineOptions pipeline={pipeline} />
      <ContractAddButton pipeline={pipeline} />
    </div>
  )
}

export default PipelineActions
