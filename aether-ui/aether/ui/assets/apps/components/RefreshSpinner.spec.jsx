/* global describe, it, expect */

import React from 'react'
import { shallow } from 'enzyme'

import RefreshSpinner from './RefreshSpinner'

describe('RefreshSpinner', () => {
  it('should render the refresh spinner', () => {
    const component = shallow(<RefreshSpinner />)
    expect(component.find('[data-qa="data-refreshing"]').exists()).toBeTruthy()
    expect(component.find('.loading-spinner')).toBeTruthy()
  })
})
