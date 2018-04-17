/* global describe, it, expect, beforeEach, afterEach */

import React from 'react'
import { mount } from 'enzyme'

import { isMounted } from './react-utils'

class Foo extends React.Component {
  render () {
    return 'foo ' + JSON.stringify(this.props)
  }
}

describe('DOM utils', () => {
  let element = null
  beforeEach(() => {
    element = document.createElement('div')
    element.id = 'my-element'
    document.body.appendChild(element)
  })

  afterEach(() => {
    document.body.removeChild(element)
  })

  describe('isMounted', () => {
    it('should return true if the component is in the DOM', () => {
      const component = mount(<Foo />, {attachTo: element})

      expect(isMounted(component.instance())).toBeTruthy()
    })

    it('should return false if the component is not in the DOM', () => {
      const component = mount(<Foo />, {attachTo: element})
      component.unmount()
      expect(isMounted(component)).toBeFalsy()
    })
  })
})
