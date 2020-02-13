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
import OutsideClickHandler from 'react-outside-click-handler'

const ModalDialog = ({ header, children, buttons, handleClickOutside: handler }) => {
  const handleClickOutside = (args) => {
    if (handler) handler(args)
  }

  return (
    <OutsideClickHandler onOutsideClick={handleClickOutside}>
      <div className='modal-dialog'>
        <div className='modal-header'>
          <span className='modal-title'>{header}</span>
        </div>

        <div className='modal-content'>
          {children}

          <div className='modal-actions'>{buttons}</div>
        </div>
      </div>
    </OutsideClickHandler>
  )
}

export default ModalDialog
