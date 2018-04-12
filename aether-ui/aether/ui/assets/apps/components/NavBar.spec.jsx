/* global describe, it, expect, beforeEach */

import React from 'react'

import { mountWithIntl } from '../../tests/test-react-intl'
import NavBar from './NavBar'

describe('NavBar', () => {
  beforeEach(() => {
    const element = document.createElement('div')
    element.id = 'logged-in-user-info'
    element.setAttribute('data-user-id', '1')
    element.setAttribute('data-user-name', 'user test')
    document.body.appendChild(element)
  })

  it('should render the nav bar', () => {
    const component = mountWithIntl(<NavBar />)
    expect(component.find('[data-qa="navbar"]').exists()).toBeTruthy()
    expect(component.find('[data-qa="navbar-user"]').exists()).toBeTruthy()
    expect(component.find('[data-qa="navbar-user"]').html()).toContain('user test')
    expect(component.find('[data-qa="navbar-breadcrumb"]').exists()).toBeFalsy()
  })

  it('should include the breadcrumb', () => {
    const component = mountWithIntl(<NavBar showBreadcrumb />)
    const breadcrumb = component.find('[data-qa="navbar-breadcrumb"]')
    expect(breadcrumb.exists()).toBeTruthy()
  })

  it('should include the breadcrumb and the children', () => {
    const component = mountWithIntl(
      <NavBar showBreadcrumb>
        breadcrumb...
      </NavBar>
    )
    const breadcrumb = component.find('[data-qa="navbar-breadcrumb"]')
    expect(breadcrumb.exists()).toBeTruthy()
    expect(breadcrumb.html()).toContain('breadcrumb...')
  })
})
