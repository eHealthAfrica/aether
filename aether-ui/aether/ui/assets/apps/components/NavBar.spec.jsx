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
import { mountWithIntl } from 'enzyme-react-intl'
import { MemoryRouter } from 'react-router'

import NavBar from './NavBar'

const mountWithRouter = (node) => mountWithIntl(<MemoryRouter>{node}</MemoryRouter>)

describe('NavBar', () => {
  beforeEach(() => {
    const element = document.createElement('div')
    element.id = 'logged-in-user-info'
    element.setAttribute('data-user-id', '1')
    element.setAttribute('data-user-name', 'user test')
    document.body.appendChild(element)
  })

  it('should render the nav bar', () => {
    const component = mountWithRouter(<NavBar />)
    expect(component.find('[data-qa="navbar"]').exists()).toBeTruthy()
    expect(component.find('[data-qa="navbar-user"]').exists()).toBeTruthy()
    expect(component.find('[data-qa="navbar-user"]').html()).toContain('user test')
    expect(component.find('[data-qa="navbar-breadcrumb"]').exists()).toBeFalsy()
  })

  it('should include the breadcrumb', () => {
    const component = mountWithRouter(<NavBar showBreadcrumb />)
    const breadcrumb = component.find('[data-qa="navbar-breadcrumb"]')
    expect(breadcrumb.exists()).toBeTruthy()
  })

  it('should include the breadcrumb and the children', () => {
    const component = mountWithRouter(
      <NavBar showBreadcrumb>
        breadcrumb...
      </NavBar>
    )
    const breadcrumb = component.find('[data-qa="navbar-breadcrumb"]')
    expect(breadcrumb.exists()).toBeTruthy()
    expect(breadcrumb.html()).toContain('breadcrumb...')
  })
})
