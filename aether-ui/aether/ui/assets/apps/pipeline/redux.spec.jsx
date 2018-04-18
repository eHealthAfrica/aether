/* global describe, it, expect, beforeEach */
import reducer, { types, selectedPipelineChanged,
  addPipeline, getPipelines, updatePipeline, INITIAL_PIPELINE } from './redux'
import { createStore, applyMiddleware } from 'redux'
import middleware from '../redux/middleware'
import mockPipelines from '../../../static/mock/pipelines.mock.json'

describe('Pipeline actions', () => {
  let store
  beforeEach(() => {
    // create a new store instance for each test
    store = createStore(
      reducer,
      applyMiddleware(...middleware)
    )
  })

  it('should return the initial redux store state', () => {
    expect(store.getState()).toEqual(
      INITIAL_PIPELINE
    )
  })

  it('should dispatch a selected pipeline changed action and update the redux store', () => {
    const selectedPipeline = { name: 'mock name', id: 1, errors: 0, entityTypes: 3 }
    const expectedAction = {
      type: types.SELECTED_PIPELINE_CHANGED,
      payload: selectedPipeline
    }
    expect(selectedPipelineChanged(selectedPipeline)).toEqual(expectedAction)
    store.dispatch(selectedPipelineChanged(selectedPipeline))
    expect(store.getState().selectedPipeline).toEqual(
      selectedPipeline
    )
  })

  it('should create an action when adding a new pipeline and store in redux', () => {
    const newPipeline = { name: 'mock new name', id: 2, errors: 0, entityTypes: 6 }
    const expectedAction = {
      type: types.PIPELINE_ADD,
      payload: newPipeline
    }
    expect(addPipeline(newPipeline)).toEqual(expectedAction)
    store.dispatch(addPipeline(newPipeline))
    expect(store.getState().pipelineList).toEqual(
      [newPipeline]
    )
  })

  it('should dispatch an update action and update redux store', () => {
    const pipeline = {
      'id': 2,
      'name': 'Pipeline Mock 2 updated',
      'errors': 0,
      'entityTypes': 3
    }
    const expectedAction = {
      type: types.PIPELINE_UPDATE,
      payload: pipeline
    }
    expect(updatePipeline(pipeline)).toEqual(expectedAction)
    return store.dispatch(getPipelines())
      .then(() => {
        store.dispatch(updatePipeline(pipeline))
        expect(store.getState().pipelineList[1]).toEqual(
          pipeline
        )
      })
  })

  it('should successfully get all pipelines and add to store', () => (
    store.dispatch(getPipelines())
      .then(() => {
        expect(store.getState().pipelineList).toEqual(
          mockPipelines
        )
      })
  ))

  it('should fail on getting all pipelines and store error', () => {
    const NotFoundUrl = 'http://localhost:8004/static/mock/nojson.json'
    const action = () => ({
      types: ['', types.GET_ALL, types.GET_ALL_FAILED],
      promise: client => client.get(NotFoundUrl)
    }) // Sample usage of request middleware (client) plugged into redux
    const expectedStoreData = {
      pipelineList: [],
      selectedPipeline: null,
      error: { error: 'Not Found', status: 404 }
    }
    return store.dispatch(action())
      .then(() => {
        expect(store.getState()).toEqual(expectedStoreData)
      })
  })
})
