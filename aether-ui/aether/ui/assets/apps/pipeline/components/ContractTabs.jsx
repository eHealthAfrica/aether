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

import React from 'react'
import { connect } from 'react-redux'

import { FormattedMessage } from 'react-intl'

import ContractAddButton from './ContractAddButton'

import { selectContract } from '../redux'

const ContractTabs = ({
  isAddingNew,
  checkUnsavedContract,
  current,
  list,
  pipeline,
  selectContract,
  showSettings,
  toggleSettings
}) => {
  return (
    <div className='pipeline-tabs'>
      {
        list.map(item => (
          <div
            key={item.id}
            className={`pipeline-tab ${!isAddingNew && item.id === current.id ? 'active' : ''}`}
            onClick={() => {
              checkUnsavedContract(() => { selectContract(pipeline.id, item.id) })
            }}
          >
            <span className='contract-name'>{item.name}</span>

            {
              (item.mapping_errors || []).length > 0 &&
                <span className={`status ${(item.mapping_errors || []).length ? 'red' : 'green'}`} />
            }

            <div
              className={`btn-icon settings-button ${showSettings ? 'active' : ''}`}
              onClick={() => { toggleSettings() }}
            >
              <i className='fas fa-wrench' />
            </div>
          </div>
        ))
      }

      {
        isAddingNew &&
          <div key='new-contract' className='pipeline-tab active'>
            <span className='contract-name new'>
              <FormattedMessage
                id='contracts.tab.new.contract'
                defaultMessage='New contract'
              />
            </span>
          </div>
      }

      {
        !isAddingNew &&
          <ContractAddButton
            className='btn btn-c btn-sm new-contract'
            pipeline={pipeline}
          />
      }
    </div>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  isAddingNew: !!pipelines.newContract,
  current: pipelines.currentContract,
  list: pipelines.currentPipeline.contracts,
  pipeline: pipelines.currentPipeline
})

const mapDispatchToProps = { selectContract }

export default connect(mapStateToProps, mapDispatchToProps)(ContractTabs)
