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
import Clipboard from 'react-clipboard.js'

export default ({ content }) => {
  const [icon, setIcon] = useState('')

  const onCopy = (event) => {
    console.log('click clipboard')
    event && event.stopPropagation()
    setIcon('-check')
    setTimeout(() => { setIcon('') }, 2000)
  }

  return (
    <span className='ms-2 clipboard'>
      <Clipboard
        component='i'
        onClick={onCopy}
        data-clipboard-text={content}
      >
        <i className={`fas fa-clipboard${icon}`} />
      </Clipboard>
    </span>
  )
}
