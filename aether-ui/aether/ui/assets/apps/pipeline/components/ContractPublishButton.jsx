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
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import moment from 'moment'

import Modal from '../../components/Modal'

import { publishPreflightContract, publishContract } from '../redux'
import { objectToString } from '../../utils'
import { DATE_FORMAT } from '../../utils/constants'

const ContractPublishButton = ({
  className,
  contract,
  publishContract,
  publishError,
  publishPreflightContract,
  publishState,
  publishSuccess
}) => {
  const [showModal, setShowModal] = useState(false)

  const renderModal = () => {
    if (!showModal) {
      return ''
    }

    let errors = []
    let warnings = []
    let infos = []

    /* Publish with success */
    if (publishSuccess) {
      infos = [
        <FormattedMessage
          key='contract.publish.status.success'
          id='contract.publish.status.success'
          defaultMessage='Contract published successfully'
        />
      ]
    }

    /* Publish with error */
    if (publishError) {
      errors = [
        <FormattedMessage
          key='contract.publish.status.error'
          id='contract.publish.status.error'
          defaultMessage='An unexpected error produced while publishing'
        />,
        (publishError.detail || objectToString(publishError))
      ]
    }

    /* Publish preflight response */
    if (publishState) {
      errors = publishState.error || []
      warnings = publishState.warning || []
      infos = publishState.info || []
    }

    const header = (
      <>
        <FormattedMessage
          id='contract.publish.header'
          defaultMessage='Publish contract'
        />: {contract.name}
      </>
    )

    const close = (event) => {
      event.stopPropagation()
      setShowModal(false)
    }
    const publish = (event) => {
      event.stopPropagation()
      publishContract(contract.id)
    }
    const closeOrPublish = (publishState && errors.length === 0) ? publish : close

    const buttons = (
      <>
        <button
          type='button'
          className='btn btn-w'
          onClick={close}
        >
          {
            publishSuccess
              ? (
                <FormattedMessage
                  id='contract.publish.button.close'
                  defaultMessage='Close'
                />)
              : (
                <FormattedMessage
                  id='contract.publish.button.cancel'
                  defaultMessage='Cancel'
                />)
          }
        </button>

        {/* show publish button only after publish preflight and without "errors" */}
        {
          publishState && errors.length === 0 &&
            <button
              type='button'
              className='btn btn-primary btn-w'
              onClick={publish}
            >
              <FormattedMessage
                id='contract.publish.button.ok'
                defaultMessage='Publish'
              />
            </button>
        }
      </>
    )

    return (
      <Modal
        buttons={buttons}
        header={header}
        onEnter={closeOrPublish}
        onEscape={close}
      >
        <label className='form-label'>
          <FormattedMessage
            id='contract.publish.status'
            defaultMessage='Publish status'
          />
          {/* Executing a request */}
          {
            !publishSuccess && !publishError && !publishState &&
              <i className='ms-5 fas fa-cog fa-spin' />
          }
        </label>

        <ul>
          {
            errors.map((msg, index) => (
              <li key={index} className='error'>{msg}</li>
            ))
          }
          {
            warnings.map((msg, index) => (
              <li key={index} className='warning'>{msg}</li>
            ))
          }
          {
            infos.map((msg, index) => (
              <li key={index} className='success'>{msg}</li>
            ))
          }
        </ul>
      </Modal>
    )
  }

  return (
    <>
      {renderModal()}

      <div>
        {
          contract.published_on &&
            <>
              <FormattedMessage
                id='contract.publish-status.published'
                defaultMessage='Published on'
              /> {moment(contract.published_on).format(DATE_FORMAT)}
            </>
        }

        {
          contract.created && !contract.published_on &&
            <FormattedMessage
              id='contract.publish-status.not-published'
              defaultMessage='Not published yet'
            />
        }
      </div>

      {
        contract.created && !contract.is_read_only &&
          <button
            type='button'
            className={className}
            onClick={(event) => {
              event.stopPropagation()
              publishPreflightContract(contract.id)
              setShowModal(true)
            }}
          >
            <FormattedMessage
              id='contract.publish.button'
              defaultMessage='Publish'
            />
          </button>
      }
    </>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  publishError: pipelines.publishError,
  publishState: pipelines.publishState,
  publishSuccess: pipelines.publishSuccess
})
const mapDispatchToProps = {
  publishPreflightContract,
  publishContract
}

export default connect(mapStateToProps, mapDispatchToProps)(ContractPublishButton)
