/* global describe, it, expect, beforeEach */
import reducer, { types, selectedPipelineChanged,
  addPipeline, getPipelines, updatePipeline, INITIAL_PIPELINE, getPipelineById } from './redux'
import { createStore, applyMiddleware } from 'redux'
import nock from 'nock'
import middleware from '../redux/middleware'
import mockPipelines from '../mock/pipelines.mock'

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
    const newPipeline = { name: 'mock new name' }
    nock('http://localhost')
      .post('/api/ui/pipelines/')
      .reply(200, Object.assign(newPipeline, { id: 'mockid' }))
    expect(typeof addPipeline(newPipeline)).toEqual('object')
    return store.dispatch(addPipeline(newPipeline))
      .then(res => {
        expect(store.getState().pipelineList[0].id).toEqual(
          'mockid'
        )
      })
  })

  it('should dispatch an update action and update redux store', () => {
    const pipeline = {
      'id': 2,
      'name': 'Pipeline Mock 2 UPDATED',
      'mapping_errors': null,
      'mapping': [],
      'output': null,
      'entity_types': [],
      'schema': null,
      'input': null
    }
    nock('http://localhost')
      .get('/api/ui/pipelines/?limit=5000')
      .reply(200, mockPipelines)

    nock('http://localhost')
      .put(`/api/ui/pipelines/${pipeline.id}/`)
      .reply(200, pipeline)
    expect(typeof updatePipeline(pipeline)).toEqual('object')
    return store.dispatch(getPipelines())
      .then(() => {
        return store.dispatch(updatePipeline(pipeline))
          .then(() => {
            expect(store.getState().pipelineList[1]).toEqual(
              pipeline
            )
          })
      })
  })

  it('should try updating pipeline with wrong id and fail', () => {
    const wrongPipeline = {
      'id': 100,
      'name': 'None existant pipeline ',
      'mapping_errors': null,
      'mapping': [],
      'output': null,
      'entity_types': [],
      'schema': null,
      'input': null
    }
    nock('http://localhost')
      .get('/api/ui/pipelines/?limit=5000')
      .reply(200, mockPipelines)

    nock('http://localhost')
      .put(`/api/ui/pipelines/${wrongPipeline.id}/`)
      .reply(404)
    expect(typeof updatePipeline(wrongPipeline)).toEqual('object')
    return store.dispatch(getPipelines())
      .then(() => {
        return store.dispatch(updatePipeline(wrongPipeline))
          .then(res => {
            expect(store.getState().error).toEqual(
              { error: 'Not Found', status: 404 }
            )
          })
      })
  })

  it('should successfully get all pipelines and add to store', () => {
    nock('http://localhost')
      .get('/api/ui/pipelines/?limit=5000')
      .reply(200, mockPipelines)
    store.dispatch({type: types.GET_ALL, payload: {}})
    expect(store.getState().pipelineList).toEqual([])
    return store.dispatch(getPipelines())
      .then(() => {
        expect(store.getState().pipelineList).toEqual(
          mockPipelines.results
        )
      })
  })

  it('should fail on getting all pipelines and store error', () => {
    nock('http://localhost')
      .get('/api/ui/nojson.json')
      .reply(404)
    const NotFoundUrl = 'http://localhost/api/ui/nojson.json'
    const action = () => ({
      types: ['', types.GET_ALL, types.PIPELINE_ERROR],
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

  it('should dispatch an action to get pipeline by id and set it as selected pipeline in the redux store', () => {
    const pipelineId = 1
    const expectedAction = {
      type: types.GET_BY_ID,
      payload: pipelineId
    }
    nock('http://localhost')
      .get('/api/ui/pipelines/?limit=5000')
      .reply(200, mockPipelines)
    expect(getPipelineById(pipelineId)).toEqual(expectedAction)
    return store.dispatch(getPipelines())
      .then(() => {
        store.dispatch(getPipelineById(pipelineId))
        expect(store.getState().selectedPipeline).toEqual(
          mockPipelines.results.filter(pipeline => (pipeline.id === pipelineId))[0]
        )
      })
  })
})
