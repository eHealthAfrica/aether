/* global describe, it, expect */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import EmptyAlert from './EmptyAlert'

describe('EmptyAlert', () => {
  it('should render the empty warning', () => {
    const component = mountWithIntl(<EmptyAlert />)
    expect(component.find('[data-qa="data-empty"]').exists()).toBeTruthy()
    expect(component.text()).toContain('Nothing to display.')
  })
})
