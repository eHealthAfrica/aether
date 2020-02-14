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

import OutsideClickHandler from 'react-outside-click-handler'
import Modal from '../../components/Modal'
import SubmissionCard from './SubmissionCard'

const PipelineInfo = ({ close, pipeline: { name, mappingset, input } }) => {
  const button = (
    <button type='button' className='btn btn-w btn-primary' onClick={close}>
      <FormattedMessage id='pipeline.info.modal.ok' defaultMessage='OK' />
    </button>
  )

  return (
    <OutsideClickHandler onOutsideClick={close}>
      <Modal
        onEnter={close}
        onEscape={close}
        header={name}
        buttons={button}
      >
        <SubmissionCard mappingset={mappingset} inputData={input} />
      </Modal>
    </OutsideClickHandler>
  )
}

export default connect()(PipelineInfo)
