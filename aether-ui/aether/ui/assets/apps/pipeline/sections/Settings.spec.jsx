/*
 * Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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

/* global describe, it, expect, beforeEach, jest */

import React from 'react'
import { createStore, applyMiddleware } from 'redux'
import { Provider } from 'react-redux'
import { mountWithIntl } from 'enzyme-react-intl'
import nock from 'nock'

import Settings from './Settings'
import { mockPipeline } from '../../../tests/mock'
import middleware from '../../redux/middleware'
import reducer from '../../redux/reducers'
import { contractChanged } from '../redux'

describe('Pipeline Settings Component', () => {
  let store
  const initialState = {
    pipelines: {
      currentPipeline: mockPipeline
    }
  }
  const onClose = jest.fn()
  const onSave = jest.fn()
  const onNew = jest.fn()

  beforeEach(() => {
    // create a new store instance for each test
    store = createStore(
      reducer,
      initialState,
      applyMiddleware(...middleware)
    )
  })

  it('should render the settings component', () => {
    const component = mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          onSave={onSave}
          onNew={onNew}
        />
      </Provider>
    )
    expect(component.find('Settings').exists()).toBeTruthy()
    expect(store.getState().pipelines.currentContract)
      .toEqual(undefined)
  })

  it('should render the settings of selected contract', () => {
    const selectedContract = mockPipeline.contracts[0]
    store.dispatch(contractChanged(selectedContract))
    const component = mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          onSave={onSave}
          onNew={onNew}
        />
      </Provider>
    )
    expect(component.find('[className="input-d contract-name"]')
      .html()).toContain(`value="${selectedContract.name}"`)
  })

  it('should render the settings with a new contract', () => {
    mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          isNew
          onSave={onSave}
          onNew={onNew}
        />
      </Provider>
    )
    expect(store.getState().pipelines.currentContract.name)
      .toEqual('Contract 0')
  })

  it('should toggle identity mapping', () => {
    const component = mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          isNew
          onSave={onSave}
          onNew={onNew}
        />
      </Provider>
    )
    expect(component.find('Settings').exists()).toBeTruthy()
    const settings = component.find('Settings')

    expect(settings.state().isIdentity).toBeFalsy()
    expect(component.find('[id="settings.contract.identity.name"]')
      .exists()).toBeFalsy()

    const identityMappingToggle = component.find('input[id="toggle"]')
    identityMappingToggle.simulate('change', { target: { checked: true } })
    expect(settings.state().isIdentity).toBeTruthy()

    expect(component.find('[id="settings.contract.identity.name"]')
      .exists()).toBeTruthy()

    identityMappingToggle.simulate('change', { target: { checked: false } })
    expect(settings.state().isIdentity).toBeFalsy()
    expect(component.find('[id="settings.contract.identity.name"]')
      .exists()).toBeFalsy()
  })

  it('should render identity mapping warning', () => {
    const component = mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          isNew
          onSave={onSave}
          onNew={onNew}
        />
      </Provider>
    )
    expect(component.find('Settings').exists()).toBeTruthy()
    const settings = component.find('Settings')

    const identityMappingToggle = component.find('input[id="toggle"]')
    identityMappingToggle.simulate('change', { target: { checked: true } })
    expect(settings.state().isIdentity).toBeTruthy()

    expect(component.find('Modal').exists()).toBeFalsy()
    const saveButton = component.find('button[className="btn btn-d btn-primary btn-big ml-4"]')
    saveButton.simulate('click')

    expect(component.find('Modal').exists()).toBeTruthy()
  })

  it('should save and close settings without warning', () => {
    const selectedContract = mockPipeline.contracts[0]
    let expectedContract
    nock('http://localhost')
      .put(`/api/contracts/${selectedContract.id}/`)
      .reply(200, (_, reqBody) => {
        expectedContract = reqBody
        return reqBody
      })

    store.dispatch(contractChanged(selectedContract))
    const component = mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          onSave={onSave}
          onNew={onNew}
        />
      </Provider>
    )
    expect(component.find('Modal').exists()).toBeFalsy()

    const inputContractName = component.find('input[className="input-d contract-name"]')
    inputContractName.simulate('change', { target: { value: 'contract-updated' } })

    const settings = component.find('Settings').instance()
    jest.spyOn(settings, 'performSave')
    const saveButton = component.find('button[className="btn btn-d btn-primary btn-big ml-4"]')
    saveButton.simulate('click')

    expect(component.find('Modal').exists()).toBeFalsy()
    expect(settings.performSave).toHaveBeenCalledWith(expectedContract)
  })

  it('should save and close settings without warning on a new contract', () => {
    let expectedContract
    nock('http://localhost')
      .post(`/api/contracts/`)
      .reply(200, (_, reqBody) => {
        expectedContract = reqBody
        return reqBody
      })

    const component = mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          onSave={onSave}
          onNew={onNew}
          isNew
        />
      </Provider>
    )
    expect(component.find('Modal').exists()).toBeFalsy()

    const inputContractName = component.find('input[className="input-d contract-name"]')
    inputContractName.simulate('change', { target: { value: 'new-contract-updated' } })

    const settings = component.find('Settings').instance()
    jest.spyOn(settings, 'performSave')
    const saveButton = component.find('button[className="btn btn-d btn-primary btn-big ml-4"]')
    saveButton.simulate('click')

    expect(component.find('Modal').exists()).toBeFalsy()
    expect(settings.performSave).toHaveBeenCalledWith(expectedContract)
  })

  it('should close the settings component', () => {
    const component = mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          onSave={onSave}
          onNew={onNew}
        />
      </Provider>
    )
    const cancelButton = component.find('button[id="pipeline.settings.cancel.button"]')
    cancelButton.simulate('click')

    expect(onClose).toBeCalled()
  })
})
