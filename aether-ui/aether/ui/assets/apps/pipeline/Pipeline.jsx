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

import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { useHistory } from 'react-router-dom'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { LoadingSpinner, Modal, NavBar } from '../components'

import Sections from './sections/Sections'
import Settings from './sections/Settings'
import ContractTabs from './components/ContractTabs'

import { clearSelection, getPipelineById, selectContract } from './redux'
import { PIPELINE_SECTION_INPUT } from '../utils/constants'

const Pipeline = ({
  pipeline,
  contract,
  section,
  newContract,
  clearSelection,
  getPipelineById,
  selectContract
}) => {
  const { pid, cid, view } = useParams()
  const history = useHistory()

  const [fullscreen, setFullscreen] = useState(false)
  const [showOutput, setShowOutput] = useState(false)
  const [showSettings, setShowSettings] = useState(!!newContract)
  const [showUnsavedWarning, setShowUnsavedWarning] = useState(false)
  const [unsavedCallback, setUnsavedCallback] = useState(null)

  useEffect(() => {
    if (!pipeline || pipeline.id !== pid) {
      getPipelineById(pid)
    } else {
      if (!newContract && contract && (section !== view || contract.id !== cid)) {
        // update router history
        history.push(`/${pipeline.id}/${contract.id}/${section}`)
      }

      if (section === PIPELINE_SECTION_INPUT) {
        setShowSettings(false)
        setShowOutput(false)
      }

      if (newContract) {
        setShowSettings(true)
      }
    }
  })

  if (!pipeline) {
    return <LoadingSpinner /> // still loading data
  }

  const checkUnsavedContract = (callback) => {
    if (newContract) {
      setShowUnsavedWarning(true)
      setUnsavedCallback(callback)
    } else {
      setShowUnsavedWarning(false)
      setUnsavedCallback(null)
      callback && callback()
    }
  }

  const backToList = () => {
    checkUnsavedContract(() => {
      history.push('/')
      clearSelection()
    })
  }

  const closeUnsavedWarning = () => { setShowUnsavedWarning(false) }
  const cancelUnsavedWarning = () => {
    setShowUnsavedWarning(false)
    setShowSettings(false)

    const nextContractId = contract
      ? contract.id
      : pipeline.contracts.length > 0
        ? pipeline.contracts[0].id
        : null

    selectContract(
      pipeline.id,
      nextContractId,
      nextContractId ? section : PIPELINE_SECTION_INPUT
    )

    unsavedCallback && unsavedCallback()
    setUnsavedCallback(null)
  }

  const unsavedWarningButtons = (
    <>
      <button
        data-test='pipeline.new.contract.continue'
        className='btn btn-w'
        onClick={closeUnsavedWarning}
      >
        <FormattedMessage
          id='pipeline.new.contract.continue.message'
          defaultMessage='No, Continue Editing'
        />
      </button>

      <button className='btn btn-w btn-primary' onClick={cancelUnsavedWarning}>
        <FormattedMessage
          id='pipeline.new.contract.cancel'
          defaultMessage='Yes, Cancel'
        />
      </button>
    </>
  )

  return (
    <div className={`pipelines-container show-pipeline pipeline--${section}`}>
      <NavBar showBreadcrumb onClick={backToList}>
        <div className='breadcrumb-links'>
          <a onClick={backToList}>
            <FormattedMessage
              id='pipeline.navbar.pipelines'
              defaultMessage='Pipelines'
            />
          </a>
          <span className='breadcrumb-pipeline-name'>
            <span>&#47;&#47; </span>
            {pipeline.name}
            {
              pipeline.isInputReadOnly &&
                <span className='tag'>
                  <FormattedMessage
                    id='pipeline.navbar.read-only'
                    defaultMessage='read-only'
                  />
                </span>
            }
          </span>
        </div>
      </NavBar>

      <div
        className={`pipeline ${showOutput ? 'show-output' : ''} ${fullscreen ? 'fullscreen' : ''}`}
      >
        <ContractTabs
          checkUnsavedContract={checkUnsavedContract}
          showSettings={showSettings}
          toggleSettings={() => { setShowSettings(!showSettings) }}
        />

        <Sections
          checkUnsavedContract={checkUnsavedContract}
          fullscreen={fullscreen}
          toggleFullscreen={() => { setFullscreen(!fullscreen) }}
          toggleOutput={() => { setShowOutput(!showOutput) }}
        />

        {
          (newContract || showSettings) &&
            <Settings
              onClose={() => { checkUnsavedContract(() => { setShowSettings(false) }) }}
              onSave={() => { setShowSettings(false) }}
            />
        }

        {
          showUnsavedWarning &&
            <Modal
              header={
                <FormattedMessage
                  id='pipeline.unsaved.contract.warning.header'
                  defaultMessage='Cancel the new contract?'
                />
              }
              buttons={unsavedWarningButtons}
              onEscape={closeUnsavedWarning}
              onEnter={cancelUnsavedWarning}
            />
        }
      </div>
    </div>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  contract: pipelines.currentContract,
  newContract: pipelines.newContract,
  pipeline: pipelines.currentPipeline,
  section: pipelines.currentSection || PIPELINE_SECTION_INPUT
})

const mapDispatchToProps = {
  clearSelection,
  getPipelineById,
  selectContract
}

export default connect(mapStateToProps, mapDispatchToProps)(Pipeline)
