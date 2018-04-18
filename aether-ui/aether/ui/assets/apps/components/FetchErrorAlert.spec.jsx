/* global describe, it, expect */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import FetchErrorAlert from './FetchErrorAlert'

describe('FetchErrorAlert', () => {
  it('should render the fetch error warning', () => {
    const component = mountWithIntl(<FetchErrorAlert />)
    expect(component.find('[data-qa="data-erred"]').exists()).toBeTruthy()
    expect(component.text()).toContain('Request was not successful')
  })
})
