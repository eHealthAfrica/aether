import React from 'react'

import { mountWithIntl } from '../../../tests/test-react-intl'
import NavBar from './NavBar'

describe('NavBar', () => {
  it('should render the nav bar', () => {
    const component = mountWithIntl(<NavBar />)
    expect(component.find('[data-qa="navbar"]').exists()).toBeTruthy()
    expect(component.find('[data-qa="navbar-breadcrumb"]').exists()).toBeFalsy()
  })

  it('should include the breadcrumb', () => {
    const component = mountWithIntl(<NavBar showBreadcrumb />, {context: { intl: [] }})
    const breadcrumb = component.find('[data-qa="navbar-breadcrumb"]')
    expect(breadcrumb.exists()).toBeTruthy()
    expect(breadcrumb.html()).toContain('PIPELINES')
    expect(breadcrumb.html()).toContain('Select a pipeline')
  })

  it('should include the breadcrumb and the pipeline name', () => {
    const component = mountWithIntl(<NavBar showBreadcrumb selectedPipeline={{name: 'test'}} />)
    const breadcrumb = component.find('[data-qa="navbar-breadcrumb"]')
    expect(breadcrumb.exists()).toBeTruthy()
    expect(breadcrumb.html()).toContain('PIPELINES')
    expect(breadcrumb.html()).toContain('test')
  })
})
