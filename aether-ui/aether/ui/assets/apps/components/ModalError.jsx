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

import Modal from './Modal'

const ModalError = ({ error }) => {
  const [showError, setShowError] = useState(true)
  if (!showError) {
    return ''
  }

  const close = (event) => {
    event.stopPropagation()
    setShowError(false)
  }

  return (
    <Modal
      onEnter={close}
      onEscape={close}
      header={
        <>
          <FormattedMessage
            id='modal.error.header'
            defaultMessage='Error code'
          /> {error.status}
        </>
      }
      buttons={
        <button
          type='button'
          className='btn btn-w btn-primary'
          onClick={close}
        >
          <FormattedMessage id='modal.error.ok' defaultMessage='OK' />
        </button>
      }
    >
      {error.message}
    </Modal>
  )
}

export default ModalError
