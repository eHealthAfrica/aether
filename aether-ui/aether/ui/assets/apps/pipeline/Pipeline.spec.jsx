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

/* global describe, it, expect, beforeEach */

import React from 'react'
import { createStore, applyMiddleware } from 'redux'
import { Provider } from 'react-redux'
import { mountWithIntl } from 'enzyme-react-intl'

import Pipeline from '../pipeline/Pipeline'
import reducer from '../redux/reducers'
import middleware from '../redux/middleware'

import {
  CONTRACT_SECTION_SETTINGS
} from '../utils/constants'

describe('Pipeline Component', () => {
  let store

  beforeEach(() => {
    // create a new store instance for each test
    store = createStore(
      reducer,
      applyMiddleware(...middleware)
    )
  })

  it('should initiate a new contract process', () => {
    const component = mountWithIntl(
      <Provider store={store}>
        <Pipeline
          location={{ state: { isNewContract: true } }}
          match={{ params: {} }} />
      </Provider>
    )
    const pipelineComponent = component.find('Pipeline')

    const reduxState = store.getState().pipelines
    const localState = pipelineComponent.state()

    expect(reduxState.currentSection).toEqual(CONTRACT_SECTION_SETTINGS)
    expect(localState.isNew).toEqual(true)
  })
})
