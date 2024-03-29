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

/* global describe, it, expect */

import React from 'react'
import { IntlProvider } from 'react-intl'
import { Provider } from 'react-redux'
import { mount } from 'enzyme'

import AppLayout from './AppLayout'

const Foo = () => 'foo'

describe('AppLayout', () => {
  it('should render the component wrapped by Redux Provider and IntlProvider', () => {
    const component = mount(<AppLayout app={Foo} />)

    expect(component.find(Provider).exists()).toBeTruthy()
    expect(component.find(IntlProvider).exists()).toBeTruthy()
    expect(component.find(Foo).exists()).toBeTruthy()
    expect(component.text()).toContain('foo')
  })
})
