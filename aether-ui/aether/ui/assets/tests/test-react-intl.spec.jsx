import React from 'react'
import { FormattedMessage } from 'react-intl'

import { shallowWithIntl, mountWithIntl, renderWithIntl } from './test-react-intl'

class Test extends React.Component {
  render () {
    return <FormattedMessage id='test.msg' />
  }
}

describe('Test with ReactIntl', () => {
  describe('shallowWithIntl', () => {
    it('should have intl prop passed to the component',  () => {
      const component = shallowWithIntl(<Test />)
      expect(component.instance().props.intl).toBeTruthy()
    })
  })

  describe('renderWithIntl', () => {
    it('should render the text',  () => {
      const component = renderWithIntl(<Test />)
      expect(component.text()).toContain('test')
    })
  })

  describe('mountWithIntl', () => {
    it('should have intl prop passed to the component and render the text', () => {
      const component = mountWithIntl(<Test />)
      expect(component.instance().props.intl).toBeTruthy()
      expect(component.text()).toContain('test')
    })
  })
})
