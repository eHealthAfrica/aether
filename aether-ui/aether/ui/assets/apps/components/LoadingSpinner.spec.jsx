/* global describe, it, expect */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import LoadingSpinner from './LoadingSpinner'

describe('LoadingSpinner', () => {
  it('should render the loading spinner', () => {
    const component = mountWithIntl(<LoadingSpinner />)
    expect(component.find('[data-qa="data-loading"]').exists()).toBeTruthy()
    expect(component.find('.loading-spinner')).toBeTruthy()
    expect(component.text()).toContain('Loading data from server…')
  })
})
