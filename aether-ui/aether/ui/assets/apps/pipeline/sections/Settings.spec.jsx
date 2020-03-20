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

/* global describe, it, expect, afterEach, beforeEach, jest */

import React from 'react'
import { createStore, applyMiddleware } from 'redux'
import { Provider } from 'react-redux'
import { mountWithIntl } from '../../../tests/enzyme-helpers'
import nock from 'nock'

import Settings from './Settings'
import { mockInputSchema } from '../../../tests/mock'
import middleware from '../../redux/middleware'
import reducer from '../../redux/reducers'
import { selectContract } from '../redux'

const INITIAL_STATE = {
  pipelines: {
    currentPipeline: {
      id: 'pid',
      name: 'pipeline',
      schema: mockInputSchema, // no identity without schema
      contracts: [
        {
          id: 'non-identity',
          name: 'Non identity',
          is_identity: false,
          created: '2020-01-01'
        },
        {
          id: 'identity',
          name: 'Identity',
          is_identity: true,
          created: '2020-01-01'
        }
      ]
    },
    newContract: {
      id: 'new',
      name: 'New'
    }
  }
}

describe('Pipeline Settings Component', () => {
  const onClose = jest.fn()
  const onSave = jest.fn()

  const mountComponent = (isNew, isIdentity = false) => {
    // create a new store instance for each test
    const store = createStore(
      reducer,
      INITIAL_STATE,
      applyMiddleware(...middleware)
    )
    if (!isNew) {
      store.dispatch(selectContract('pid', isIdentity ? 'identity' : 'non-identity'))
      expect(store.getState().newContract).toBeFalsy()
    }

    return mountWithIntl(
      <Provider store={store}>
        <Settings
          onClose={onClose}
          onSave={onSave}
        />
      </Provider>
    )
  }

  describe('on new contracts', () => {
    let newComponent
    beforeEach(() => {
      newComponent = mountComponent(true)
    })

    afterEach(() => {
      nock.isDone()
      nock.cleanAll()
    })

    it('should render the settings component', () => {
      expect(newComponent.find('[data-test="contract-settings"]').exists())
        .toBeTruthy()
    })

    it('should close the settings component', () => {
      const cancelButton = newComponent.find('button[data-test="settings.cancel.button"]')
      cancelButton.simulate('click')
      expect(onClose).toBeCalled()
    })

    it('should render the identity toggle', () => {
      expect(newComponent.find('[data-test="settings.contract.name"]').html())
        .toContain('value="New"')
      expect(newComponent.find('[data-test="contract.is-identity"]').exists())
        .toBeFalsy()
      expect(newComponent.find('[data-test="contract.is-not-identity"]').exists())
        .toBeTruthy()
    })

    it('should toggle identity contract', () => {
      expect(newComponent.find('[data-test="identity.contract.entity.type.name"]').exists())
        .toBeFalsy()

      const identityToggle = newComponent.find('input[data-test="identity-toggle"]')
      identityToggle.simulate('change', { target: { checked: true } })
      expect(newComponent.find('[data-test="identity.contract.entity.type.name"]').exists())
        .toBeTruthy()

      identityToggle.simulate('change', { target: { checked: false } })
      expect(newComponent.find('[data-test="identity.contract.entity.type.name"]').exists())
        .toBeFalsy()
    })

    it('should save and close settings without warning', () => {
      let newContract
      nock('http://localhost')
        .post('/api/contracts/', body => {
          newContract = body
          return body
        })
        .reply(201, {})

      const inputContractName = newComponent.find('input[data-test="settings.contract.name"]')
      inputContractName.simulate('change', { target: { value: 'new-contract-updated' } })

      const saveButton = newComponent.find('button[data-test="settings.save.button"]')
      saveButton.simulate('click')
      expect(onSave).toBeCalled()
      expect(newContract).toEqual({ id: 'new', name: 'new-contract-updated' })
    })
  })

  describe('on current non-identity contracts', () => {
    let nonIdComponent
    beforeEach(() => {
      nonIdComponent = mountComponent(false, false)
    })

    afterEach(() => {
      nock.isDone()
      nock.cleanAll()
    })

    it('should render the settings component', () => {
      expect(nonIdComponent.find('[data-test="contract-settings"]').exists())
        .toBeTruthy()
    })

    it('should close the settings component', () => {
      const cancelButton = nonIdComponent.find('button[data-test="settings.cancel.button"]')
      cancelButton.simulate('click')
      expect(onClose).toBeCalled()
    })

    it('should render the identity toggle', () => {
      expect(nonIdComponent.find('[data-test="settings.contract.name"]').html())
        .toContain('value="Non identity"')
      expect(nonIdComponent.find('[data-test="contract.is-identity"]').exists())
        .toBeFalsy()
      expect(nonIdComponent.find('[data-test="contract.is-not-identity"]').exists())
        .toBeTruthy()
    })

    it('should toggle identity contract', () => {
      expect(nonIdComponent.find('[data-test="identity.contract.entity.type.name"]').exists())
        .toBeFalsy()

      const identityToggle = nonIdComponent.find('input[data-test="identity-toggle"]')
      identityToggle.simulate('change', { target: { checked: true } })
      expect(nonIdComponent.find('[data-test="identity.contract.entity.type.name"]').exists())
        .toBeTruthy()

      identityToggle.simulate('change', { target: { checked: false } })
      expect(nonIdComponent.find('[data-test="identity.contract.entity.type.name"]').exists())
        .toBeFalsy()
    })

    it('should save and close settings without warning (while non identity)', () => {
      let updatedContract
      nock('http://localhost')
        .put('/api/contracts/non-identity/', body => {
          updatedContract = body
          return body
        })
        .reply(200, {})

      const inputContractName = nonIdComponent.find('input[data-test="settings.contract.name"]')
      inputContractName.simulate('change', { target: { value: 'non-contract-updated' } })

      const saveButton = nonIdComponent.find('button[data-test="settings.save.button"]')
      saveButton.simulate('click')
      expect(onSave).toBeCalled()
      expect(updatedContract.name).toEqual('non-contract-updated')
      expect(updatedContract.is_identity).toBeFalsy()
    })

    it('should render identity contract warning', () => {
      let updatedContract
      nock('http://localhost')
        .put('/api/contracts/non-identity/', body => {
          updatedContract = body
          return body
        })
        .reply(200, {})

      const saveButton = nonIdComponent.find('button[data-test="settings.save.button"]')
      const identityToggle = nonIdComponent.find('input[data-test="identity-toggle"]')

      identityToggle.simulate('change', { target: { checked: true } })
      expect(nonIdComponent.find('Modal').exists()).toBeFalsy()

      saveButton.simulate('click')
      expect(nonIdComponent.find('Modal').exists()).toBeTruthy()

      const modalCancelButton = nonIdComponent
        .find('Modal')
        .find('button[data-test="identity.warning.button.cancel"]')
      expect(modalCancelButton.exists()).toBeTruthy()

      modalCancelButton.simulate('click')
      expect(nonIdComponent.find('Modal').exists()).toBeFalsy()

      saveButton.simulate('click')
      expect(nonIdComponent.find('Modal').exists()).toBeTruthy()

      const modalYesButton = nonIdComponent
        .find('Modal')
        .find('button[data-test="identity.warning.button.confirm"]')
      expect(modalYesButton.exists()).toBeTruthy()

      modalYesButton.simulate('click')
      expect(nonIdComponent.find('Modal').exists()).toBeFalsy()
      expect(updatedContract.is_identity).toBeTruthy()
    })
  })

  describe('on current identity contracts', () => {
    let idComponent
    beforeEach(() => {
      idComponent = mountComponent(false, true)
    })

    afterEach(() => {
      nock.isDone()
      nock.cleanAll()
    })

    it('should render the settings component', () => {
      expect(idComponent.find('[data-test="contract-settings"]').exists())
        .toBeTruthy()
    })

    it('should close the settings component', () => {
      const cancelButton = idComponent.find('button[data-test="settings.cancel.button"]')
      cancelButton.simulate('click')
      expect(onClose).toBeCalled()
    })

    it('should not render the identity toggle', () => {
      expect(idComponent.find('[data-test="settings.contract.name"]').html())
        .toContain('value="Identity"')
      expect(idComponent.find('[data-test="contract.is-identity"]').exists())
        .toBeTruthy()
      expect(idComponent.find('[data-test="contract.is-not-identity"]').exists())
        .toBeFalsy()
    })

    it('should save and close settings without warning', () => {
      let updatedContract
      nock('http://localhost')
        .put('/api/contracts/identity/', body => {
          updatedContract = body
          return body
        })
        .reply(200, {})

      const inputContractName = idComponent.find('input[data-test="settings.contract.name"]')
      inputContractName.simulate('change', { target: { value: 'contract-updated' } })

      const saveButton = idComponent.find('button[data-test="settings.save.button"]')
      saveButton.simulate('click')
      expect(onSave).toBeCalled()
      expect(updatedContract.name).toEqual('contract-updated')
    })
  })
})
