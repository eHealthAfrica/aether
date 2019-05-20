/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

/* global describe, it, expect, beforeEach */

import { createStore, applyMiddleware } from 'redux'
import nock from 'nock'

import reducer, {
  INITIAL_STATE,
  types,

  addPipeline,
  getPipelineById,
  getPipelines,
  publishContract,
  selectContract,
  selectPipeline,
  updatePipeline
} from './redux'

import middleware from '../redux/middleware'

const mockPipelines = [
  {
    id: 1,
    name: 'Pipeline Mock 1',
    is_read_only: false,
    contracts: [
      {
        id: '1-1',
        name: 'contract 1.1',
        is_read_only: false,
        pipeline: 1
      }
    ]
  },
  {
    id: 2,
    name: 'Pipeline Mock 2',
    is_read_only: false,
    contracts: [
      {
        id: '2-1',
        name: 'contract 2.1',
        is_read_only: false,
        pipeline: 2
      }
    ]
  },
  {
    id: 3,
    name: 'Pipeline Mock 3',
    is_read_only: false,
    contracts: [
      {
        id: '3-1',
        name: 'contract 3.1',
        is_read_only: false,
        pipeline: 3
      }
    ]
  }
]

describe('Pipeline actions', () => {
  let store

  beforeEach(() => {
    // set the token value for the API calls
    const tokenValue = 'CSRF-Token-Value'
    document.querySelector = (selector) => {
      expect(selector).toEqual('[name=csrfmiddlewaretoken]')
      return { value: tokenValue }
    }

    // create a new store instance for each test
    store = createStore(
      reducer,
      applyMiddleware(...middleware)
    )
  })

  it('should return the initial redux store state', () => {
    expect(store.getState()).toEqual(INITIAL_STATE)
  })

  it('should create an action when adding a new pipeline and store in redux', () => {
    nock('http://localhost')
      .post('/api/pipelines/')
      .reply(200, { id: 'mockid', contracts: [] })

    expect(store.getState().pipelineList.length).toEqual(0)

    return store.dispatch(addPipeline({ name: 'mock new name' }))
      .then(() => {
        expect(store.getState().pipelineList.length).toEqual(1)
        expect(store.getState().pipelineList[0].id).toEqual('mockid')
      })
  })

  it('should get all pipelines and add to store', () => {
    nock('http://localhost')
      .post(`/api/pipelines/fetch/`)
      .reply(200, mockPipelines)

    expect(store.getState().pipelineList.length).toEqual(0)

    return store.dispatch(getPipelines())
      .then(() => {
        expect(store.getState().pipelineList.length).toEqual(3)

        expect(store.getState().pipelineList).toEqual(
          mockPipelines.map(pipeline => ({
            ...pipeline,
            isInputReadOnly: false, // added by "parsePipeline"
            contracts: pipeline.contracts.map(contract => ({
              ...contract,
              highlightDestination: [], // added by "parseContract"
              highlightSource: {} // added by "parseContract"
            }))
          }))
        )
      })
  })

  it('should fail on getting all pipelines and store error', () => {
    nock('http://localhost')
      .post(`/api/pipelines/fetch/`)
      .reply(404)

    return store.dispatch(getPipelines())
      .then(() => {
        expect(store.getState().error).toBeTruthy()
        expect(store.getState().error.status).toEqual(404)
      })
  })

  it('should dispatch a select pipeline action and update the redux store', () => {
    const expectedAction = {
      type: types.PIPELINE_SELECT,
      payload: 1
    }
    expect(selectPipeline(1)).toEqual(expectedAction)

    nock('http://localhost')
      .post(`/api/pipelines/fetch/`)
      .reply(200, mockPipelines)

    return store.dispatch(getPipelines())
      .then(() => {
        expect(store.getState().currentPipeline).toBeFalsy()
        expect(store.getState().currentContract).toBeFalsy()

        store.dispatch(selectPipeline(1))
        expect(store.getState().currentPipeline).toBeTruthy()
        expect(store.getState().currentContract).toBeTruthy()

        expect(store.getState().currentPipeline.id).toEqual(1)
        expect(store.getState().currentContract.id).toEqual('1-1')
      })
  })

  it('should dispatch a select contract action and update the redux store', () => {
    const expectedAction = {
      type: types.CONTRACT_SELECT,
      payload: { pipeline: 2, contract: '2-1' }
    }
    expect(selectContract(2, '2-1')).toEqual(expectedAction)

    nock('http://localhost')
      .post(`/api/pipelines/fetch/`)
      .reply(200, mockPipelines)

    return store.dispatch(getPipelines())
      .then(() => {
        expect(store.getState().currentPipeline).toBeFalsy()
        expect(store.getState().currentContract).toBeFalsy()

        store.dispatch(selectPipeline(2, '2-1'))
        expect(store.getState().currentPipeline).toBeTruthy()
        expect(store.getState().currentContract).toBeTruthy()

        expect(store.getState().currentPipeline.id).toEqual(2)
        expect(store.getState().currentContract.id).toEqual('2-1')
      })
  })

  it('should dispatch an update action and update redux store I', () => {
    const pipeline = {
      id: 1,
      name: 'Pipeline Mock 1 Updated',
      contracts: [
        { pipeline: 1, id: '1-1-a', name: 'Another name' }
      ]
    }

    nock('http://localhost')
      .post(`/api/pipelines/fetch/`)
      .reply(200, mockPipelines)

    nock('http://localhost')
      .put(`/api/pipelines/1/`)
      .reply(200, pipeline)

    return store.dispatch(getPipelines())
      .then(() => {
        expect(store.getState().currentPipeline).toBeFalsy()
        expect(store.getState().currentContract).toBeFalsy()

        return store.dispatch(updatePipeline({ id: 1 }))
          .then(() => {
            expect(store.getState().currentPipeline).toBeTruthy()
            expect(store.getState().currentContract).toBeTruthy()

            expect(store.getState().currentPipeline.id).toEqual(1)
            expect(store.getState().currentPipeline.name).toEqual('Pipeline Mock 1 Updated')

            expect(store.getState().currentContract.id).toEqual('1-1-a')
            expect(store.getState().currentContract.name).toEqual('Another name')

            // the pipelines list was also updated
            const newPipelineList = store.getState().pipelineList
            expect(newPipelineList[0].name).toEqual('Pipeline Mock 1 Updated')
            expect(newPipelineList[0].contracts[0].name).toEqual('Another name')
          })
      })
  })

  it('should dispatch an update action and update redux store II', () => {
    const pipeline = {
      id: 1,
      name: 'Pipeline Mock 1 Updated',
      contracts: [
        { pipeline: 1, id: '1-1-a', name: 'Another name' }
      ]
    }
    nock('http://localhost')
      .put(`/api/pipelines/1/`)
      .reply(200, pipeline)

    expect(store.getState().pipelineList).toEqual([])
    expect(store.getState().currentPipeline).toBeFalsy()
    expect(store.getState().currentContract).toBeFalsy()

    return store.dispatch(updatePipeline({ id: 1 }))
      .then(() => {
        expect(store.getState().currentPipeline).toBeTruthy()
        expect(store.getState().currentContract).toBeTruthy()

        expect(store.getState().currentPipeline.id).toEqual(1)
        expect(store.getState().currentPipeline.name).toEqual('Pipeline Mock 1 Updated')

        expect(store.getState().currentContract.id).toEqual('1-1-a')
        expect(store.getState().currentContract.name).toEqual('Another name')

        // the pipelines list was not updated (is still empty)
        expect(store.getState().pipelineList).toEqual([])
      })
  })

  it('should try updating pipeline with wrong id and fail', () => {
    nock('http://localhost')
      .put(`/api/pipelines/4/`)
      .reply(404)

    return store.dispatch(updatePipeline({ id: 4 }))
      .then(() => {
        expect(store.getState().error).toBeTruthy()
        expect(store.getState().error.status).toEqual(404)
      })
  })

  it('should dispatch an action to get pipeline by id and set it as selected pipeline in the redux store', () => {
    const pipeline = {
      id: 3,
      name: 'Pipeline Mock 3',
      contracts: [
        {
          pipeline: 3,
          id: '3-1'
        }
      ]
    }

    nock('http://localhost')
      .get(`/api/pipelines/3/`)
      .reply(200, pipeline)

    return store.dispatch(getPipelineById(3))
      .then(() => {
        expect(store.getState().currentPipeline.id).toEqual(3)
        expect(store.getState().currentContract.id).toEqual('3-1')
      })
  })

  it('should dispatch a publish contract action and save response in the redux store', () => {
    const pipeline = {
      id: 3,
      name: 'Pipeline Mock 3',
      contracts: [
        {
          pipeline: 3,
          id: '3-1'
        }
      ]
    }

    nock('http://localhost')
      .get(`/api/pipelines/3/`)
      .reply(200, pipeline)

    nock('http://localhost')
      .post(`/api/contracts/3-1/publish/`)
      .reply(200, pipeline.contracts[0])

    return store.dispatch(getPipelineById(3))
      .then(() => {
        return store.dispatch(publishContract('3-1'))
          .then(() => {
            expect(store.getState().publishError).toBeFalsy()
            expect(store.getState().publishState).toBeFalsy()
            expect(store.getState().publishSuccess).toBeTruthy()
          })
      })
  })

  it('should dispatch a wrong publish contract action and save response in the redux store', () => {
    const pipeline = {
      id: 3,
      name: 'Pipeline Mock 3',
      contracts: [
        {
          pipeline: 3,
          id: '3-1'
        }
      ]
    }

    const returnedData = {
      error: ['error 1']
    }

    nock('http://localhost')
      .get(`/api/pipelines/3/`)
      .reply(200, pipeline)

    nock('http://localhost')
      .post('/api/contracts/3-1/publish/')
      .reply(400, returnedData)

    return store.dispatch(getPipelineById(3))
      .then(() => {
        return store.dispatch(publishContract('3-1'))
          .then(() => {
            expect(store.getState().publishError).toEqual(returnedData)
            expect(store.getState().publishState).toBeFalsy()
            expect(store.getState().publishSuccess).toBeFalsy()
          })
      })
  })
})
