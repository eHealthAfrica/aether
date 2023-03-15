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

import React from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'
import { useHistory } from 'react-router-dom'

import { Fullscreen } from '../../components'

import Input from './Input'
import EntityTypes from './EntityTypes'
import Mapping from './Mapping'
import Output from './Output'

import {
  PIPELINE_SECTION_INPUT,
  CONTRACT_SECTION_ENTITY_TYPES,
  CONTRACT_SECTION_MAPPING
} from '../../utils/constants'

import { selectSection, startNewContract } from '../redux'

const Sections = ({
  checkUnsavedContract,
  pipeline,
  contract,
  selectSection,
  fullscreen,
  toggleFullscreen,
  toggleOutput,
  startNewContract
}) => {
  if (!pipeline) return ''

  const history = useHistory()
  const showInput = () => {
    checkUnsavedContract(() => { selectSection(PIPELINE_SECTION_INPUT) })
  }
  const showContracts = () => {
    if (pipeline.contracts.length === 0) {
      startNewContract(pipeline.id)
      history.push(`/${pipeline.id}`)
    } else {
      selectSection(CONTRACT_SECTION_ENTITY_TYPES)
    }
  }

  return (
    <>
      <div className='pipeline-nav'>
        <div className='pipeline-nav-items'>
          <div className='pipeline-nav-item--input' onClick={showInput}>
            <div className='badge'>
              <i className='fas fa-file' />
            </div>
            <FormattedMessage
              id='sections.bar.input'
              defaultMessage='Input'
            />
          </div>

          <div className='pipeline-nav-item--contracts' onClick={showContracts}>
            <div className='badge'>
              <i className='fas fa-caret-right' />
            </div>
            <FormattedMessage
              id='sections.bar.contracts'
              defaultMessage='Contracts'
            />
          </div>

          <div
            className='pipeline-nav-item--entities'
            onClick={() => { selectSection(CONTRACT_SECTION_ENTITY_TYPES) }}
          >
            <div className='badge'>
              <i className='fas fa-caret-right' />
            </div>
            <FormattedMessage
              id='sections.bar.entity.types'
              defaultMessage='Entity Types'
            />
          </div>

          <div
            className='pipeline-nav-item--mapping'
            onClick={() => { selectSection(CONTRACT_SECTION_MAPPING) }}
          >
            <div className='badge'>
              <i className='fas fa-caret-right' />
            </div>
            <FormattedMessage
              id='sections.bar.mapping'
              defaultMessage='Mapping'
            />
          </div>
        </div>

        <div className='pipeline-nav-item--output' onClick={() => { toggleOutput() }}>
          <div className='badge'>
            <i className='fas fa-caret-right' />
          </div>
          <FormattedMessage
            id='sections.bar.output'
            defaultMessage='Output'
          />
          {
            ((contract && contract.mapping_errors) || []).length > 0 &&
              <span className={`status ${(contract.mapping_errors || []).length ? 'red' : 'green'}`} />
          }
        </div>
      </div>

      <div className='pipeline-sections'>
        <div className='pipeline-section--input'><Input /></div>
        {
          contract &&
            <>
              <div className='pipeline-section--entities'>
                <EntityTypes />
                <Fullscreen value={fullscreen} toggle={toggleFullscreen} />
              </div>
              <div className='pipeline-section--mapping'>
                <Mapping />
                <Fullscreen value={fullscreen} toggle={toggleFullscreen} />
              </div>
            </>
        }
      </div>
      {contract && <div className='pipeline-output'><Output /></div>}
    </>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  pipeline: pipelines.currentPipeline,
  contract: pipelines.currentContract
})
const mapDispatchToProps = { selectSection, startNewContract }

export default connect(mapStateToProps, mapDispatchToProps)(Sections)
