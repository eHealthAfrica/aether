/* global describe, it, expect */
import { types, selectedPipelineChanged } from './redux'
describe('Pipeline redux', () => {
  it('should be a function', () => {
    expect(typeof client).toEqual('function')
  })
})

describe('Pipeline actions', () => {
  it('should create an action when selected pipeline is changed', () => {
    const selectedPipeline = { name: 'mock name', id: 1, errors: 0, entityTypes: 3 }
    const expectedAction = {
      type: types.SELECTED_PIPELINE_CHANGED,
      payload: selectedPipeline
    }
    expect(selectedPipelineChanged(selectedPipeline)).toEqual(expectedAction)
  })
})
