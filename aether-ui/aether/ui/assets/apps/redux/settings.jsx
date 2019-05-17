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

import { KERNEL_URL } from '../utils/constants'

const types = {
  GET_KERNEL_URL: 'get_kernel_url',
  GET_KERNEL_URL_ERROR: 'get_kernel_url_error'
}

const INITIAL_CONST = {
  kernelUrl: ''
}

export const getKernelURL = () => ({
  types: ['', types.GET_KERNEL_URL, ''],
  promise: client => client.get(KERNEL_URL)
})

const reducer = (state = INITIAL_CONST, action) => {
  switch (action.type) {
    case types.GET_KERNEL_URL: {
      return { ...state, kernelUrl: action.payload }
    }

    default:
      return state
  }
}

export default reducer
