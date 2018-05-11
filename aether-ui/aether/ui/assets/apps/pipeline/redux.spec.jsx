/* global describe, it, expect, beforeEach */
import reducer, { types, selectedPipelineChanged,
  addPipeline, getPipelines, updatePipeline, INITIAL_PIPELINE, getPipelineById, publishPipeline } from './redux'
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
      error: { error: 'Not Found', status: 404 },
      notFound: null,
      publishSuccess: null,
      publishError: null
    }
    return store.dispatch(action())
      .then(() => {
        expect(store.getState()).toEqual(expectedStoreData)
      })
  })

  it('should dispatch an action to get pipeline by id and set it as selected pipeline in the redux store', () => {
    const pipeline = {
      'id': 1,
      'name': 'Pipeline Mock 1 From API',
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
      .get(`/api/ui/pipelines/${pipeline.id}/`)
      .reply(200, pipeline)
    expect(typeof getPipelineById(pipeline.id)).toEqual('object')
    return store.dispatch(getPipelines())
      .then(() => {
        return store.dispatch(getPipelineById(pipeline.id))
          .then(() => {
            expect(store.getState().selectedPipeline).toEqual(
              pipeline
            )
          })
      })
  })

  it('should dispatch a publish pipeline action and save response in the redux store', () => {
    const expected = {
      links: {},
      info: {}
    }
    nock('http://localhost')
      .post('/api/ui/pipelines/1/publish/')
      .reply(200, expected)
    expect(typeof publishPipeline(1)).toEqual('object')
    return store.dispatch(publishPipeline(1))
      .then(() => {
        expect(store.getState().publishSuccess).toEqual(
          expected
        )
        expect(store.getState().publishError).toEqual(
          null
        )
      })
  })

  it('should dispatch a wrong publish pipeline action and save response in the redux store', () => {
    const returnedData = {
      links: {},
      info: {}
    }
    const expected = {'error': {'info': {}, 'links': {}}, 'status': 400}
    nock('http://localhost')
      .post('/api/ui/pipelines/100/publish/')
      .reply(400, returnedData)
    return store.dispatch(publishPipeline(100))
      .then(() => {
        expect(store.getState().publishError).toEqual(
          expected
        )
        expect(store.getState().publishSuccess).toEqual(
          null
        )
      })
  })
})
