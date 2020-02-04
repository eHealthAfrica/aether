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
import { FormattedMessage } from 'react-intl'
import onClickOutside from 'react-onclickoutside'

const PipelineOptions = ({ remove, rename }) => {
  const [show, setShow] = useState(false)

  PipelineOptions.handleClickOutside = () => { setShow(false) }

  return (
    <div>
      <button
        type='button'
        className='btn btn-c btn-square mr-2'
        onClick={() => { setShow(!show) }}
      >
        <span className='details-title'>
          <i className='fas fa-ellipsis-h' />
        </span>
      </button>
      {
        show &&
          <ul className='options'>
            <li onClick={() => { remove() }}>
              <FormattedMessage
                id='pipeline.option.delete'
                defaultMessage='Delete Pipeline'
              />
            </li>
            <li onClick={() => { rename() }}>
              <FormattedMessage
                id='pipeline.option.rename'
                defaultMessage='Rename Pipeline'
              />
            </li>
          </ul>
      }
    </div>
  )
}

export default onClickOutside(PipelineOptions)
