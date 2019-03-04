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

/* global describe, expect, it, jest */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import Modal from '../../components/Modal'
import { IdentityMapping } from './Settings'

const schema = {
  type: 'record',
  name: 'Test',
  fields: [
    {
      name: 'a',
      type: ['null', 'string']
    }
    // there is no "id" field !!!
  ]
}

const contract = {
  is_read_only: false
}

describe('IdentityMapping component', () => {
  it('triggers pipeline updates and closes modal', () => {
    const updateContractMock = jest.fn()
    const component = mountWithIntl(
      <IdentityMapping
        inputSchema={schema}
        contract={contract}
        updateContract={updateContractMock}
      />
    )

    expect(component.find(Modal).length).toEqual(0)
    global.findByDataQa(component, 'contract.identity.button.apply').simulate('click')
    expect(component.find(Modal).length).toEqual(1)
    global.findByDataQa(component, 'contract.identity.button.confirm').simulate('click')
    expect(component.find(Modal).length).toEqual(0)

    expect(updateContractMock).toHaveBeenCalledTimes(1)

    const {
      mapping_rules: mappingRules,
      entity_types: entityTypes
    } = updateContractMock.mock.calls[0][0]

    expect(mappingRules[0].source).toEqual('$.a')
    expect(mappingRules[0].destination).toEqual('Test.a')

    // added the "id" rule
    expect(mappingRules[1].source).toEqual('#!uuid')
    expect(mappingRules[1].destination).toEqual('Test.id')

    expect(entityTypes.length).toEqual(1) // only one Entity Type
    expect(entityTypes[0]).toEqual({
      type: 'record',
      name: 'Test',
      fields: [
        {
          name: 'a',
          type: ['null', 'string']
        },
        {
          name: 'id',
          type: 'string'
        }
      ]
    })
  })

  it('opens modal', () => {
    const component = mountWithIntl(
      <IdentityMapping inputSchema={schema} contract={contract} />
    )

    expect(component.find(Modal).length).toEqual(0)
    global.findByDataQa(component, 'contract.identity.button.apply').simulate('click')
    expect(component.find(Modal).length).toEqual(1)
  })
})
