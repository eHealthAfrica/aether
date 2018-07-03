/* global describe, it, expect */
import React from 'react'
import { shallow } from 'enzyme'
import AppLayout from './AppLayout'
import PipelineApp from '../pipeline/PipelineApp'

describe('AppLayout', () => {
  it('should load applayout with pipeline app', () => {
    const component = shallow(<AppLayout app={PipelineApp} />)
    expect(component.exists(<div class='pipelines-container show-index' />)).toBe(true)
  })
})
