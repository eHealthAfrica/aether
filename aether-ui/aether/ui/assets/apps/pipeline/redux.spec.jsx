/*
 * Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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
// import nock from 'nock'

import reducer, {
  INITIAL_PIPELINE
  // types,

  // addPipeline,
  // getPipelineById,
  // getPipelines,
  // publishContract,
  // selectContract,
  // selectPipeline,
  // updatePipeline
} from './redux'

import middleware from '../redux/middleware'
// import { mockPipelines } from '../../tests/mock'

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
    expect(store.getState()).toEqual(INITIAL_PIPELINE)
  })

  // it('should dispatch a selected pipeline changed action and update the redux store', () => {
  //   const pipeline = {
  //     id: 1,
  //     contracts: [
  //       {
  //         id: 2,
  //         pipeline: 1
  //       }
  //     ]
  //   }
  //   const expectedAction = {
  //     type: types.PIPELINE_SELECT,
  //     payload: pipeline.id
  //   }

  //   expect(selectPipeline(pipeline.id)).toEqual(expectedAction)
  //   store.dispatch(selectPipeline(pipeline.id))
  //   expect(store.getState().currentPipeline.id).toEqual(1)
  //   expect(store.getState().currentContract.id).toEqual(2)
  // })

  // it('should create an action when adding a new pipeline and store in redux', () => {
  //   const newPipeline = { name: 'mock new name' }

  //   nock('http://localhost')
  //     .post('/api/pipelines/')
  //     .reply(200, Object.assign(newPipeline, { id: 'mockid', 'contracts': [] }))

  //   expect(typeof addPipeline(newPipeline)).toEqual('object')

  //   return store.dispatch(addPipeline(newPipeline))
  //     .then(() => {
  //       expect(store.getState().pipelineList[0].id).toEqual('mockid')
  //     })
  // })

  // it('should dispatch an update action and update redux store', () => {
  //   const pipeline = {
  //     id: 1,
  //     name: 'Pipeline Mock 1 Updated',
  //     schema: null,
  //     input: null,
  //     contracts: [
  //       {
  //         pipeline: 1,
  //         mapping_errors: null,
  //         mapping_rules: [],
  //         output: null,
  //         entity_types: [],
  //         id: '124356323',
  //         name: 'contract 1'
  //       }
  //     ]
  //   }

  //   nock('http://localhost')
  //     .get(`/api/pipelines/?limit=${MAX_PAGE_SIZE}`)
  //     .reply(200, mockPipelines)

  //   nock('http://localhost')
  //     .put(`/api/pipelines/${pipeline.id}/`)
  //     .reply(200, pipeline)

  //   expect(typeof updatePipeline(pipeline)).toEqual('object')
  //   return store.dispatch(getPipelines())
  //     .then(() => {
  //       return store.dispatch(updatePipeline(pipeline))
  //         .then(() => {
  //           const proContracts = pipeline.contracts.map(contract => (
  //             {
  //               ...contract,
  //               highlightDestination: [],
  //               highlightSource: {}
  //             })
  //           )
  //           expect(store.getState().pipelineList[0]).toEqual(
  //             { ...pipeline, contracts: proContracts, isInputReadOnly: false }
  //           )
  //         })
  //     })
  // })

  // it('should try updating pipeline with wrong id and fail', () => {
  //   const wrongPipeline = {
  //     id: 1001,
  //     name: 'Pipeline Mock 1',
  //     schema: null,
  //     input: null,
  //     contracts: [
  //       {
  //         pipeline: 1001,
  //         mapping_errors: null,
  //         mapping_rules: [],
  //         output: null,
  //         entity_types: [],
  //         id: '124356323',
  //         name: 'contract 1'
  //       }
  //     ]
  //   }

  //   nock('http://localhost')
  //     .get(`/api/pipelines/?limit=${MAX_PAGE_SIZE}`)
  //     .reply(200, mockPipelines)

  //   nock('http://localhost')
  //     .put(`/api/pipelines/${wrongPipeline.id}/`)
  //     .reply(404)

  //   expect(typeof updatePipeline(wrongPipeline)).toEqual('object')

  //   return store.dispatch(getPipelines())
  //     .then(() => {
  //       return store.dispatch(updatePipeline(wrongPipeline))
  //         .then(res => {
  //           expect(store.getState().error).toEqual(
  //             { error: 'Not Found', message: 'Resource Not Found', status: 404 }
  //           )
  //         })
  //     })
  // })

  // it('should successfully get all pipelines and add to store', () => {
  //   nock('http://localhost')
  //     .get(`/api/pipelines/?limit=${MAX_PAGE_SIZE}`)
  //     .reply(200, mockPipelines)

  //   store.dispatch({ type: types.GET_ALL, payload: [] })
  //   expect(store.getState().pipelineList).toEqual([])

  //   return store.dispatch(getPipelines())
  //     .then(() => {
  //       expect(store.getState().pipelineList).toEqual(
  //         mockPipelines.map(p => ({
  //           ...p,
  //           isInputReadOnly: false,
  //           contracts: p.contracts.map(c => ({
  //             ...c,
  //             highlightDestination: [],
  //             highlightSource: {}
  //           }))
  //         }))
  //       )
  //     })
  // })

  // it('should fail on getting all pipelines and store error', () => {
  //   nock('http://localhost')
  //     .get('/api/nojson.json')
  //     .reply(404)

  //   const NotFoundUrl = 'http://localhost/api/nojson.json'
  //   const action = () => ({
  //     types: ['', types.GET_ALL, types.REQUEST_ERROR],
  //     promise: client => client.get(NotFoundUrl)
  //   }) // Sample usage of request middleware (client) plugged into redux
  //   const expectedStoreData = {
  //     pipelineList: [],
  //     currentPipeline: null,
  //     currentContract: null,
  //     error: { error: 'Not Found', message: 'Resource Not Found', status: 404 },
  //     notFound: null,
  //     publishSuccess: null,
  //     publishError: null
  //   }

  //   return store.dispatch(action())
  //     .then(() => {
  //       expect(store.getState()).toEqual(expectedStoreData)
  //     })
  // })

  // it('should dispatch an action to get pipeline and contract by id and set it as selected pipeline in the redux store', () => {
  //   const pipeline = {
  //     id: 3,
  //     name: 'Pipeline Mock 3',
  //     contracts: [
  //       {
  //         pipeline: 3,
  //         mapping_errors: null,
  //         mapping_rules: [],
  //         output: null,
  //         entity_types: [],
  //         id: '124356323',
  //         name: 'contract 3'
  //       }
  //     ],
  //     schema: null,
  //     input: null
  //   }

  //   nock('http://localhost')
  //     .get(`/api/pipelines/${pipeline.id}/`)
  //     .reply(200, pipeline)

  //   expect(typeof getPipelineById(pipeline.id, pipeline.contracts[0].id)).toEqual('object')

  //   return store.dispatch(getPipelineById(pipeline.id, pipeline.contracts[0].id))
  //     .then(() => {
  //       expect(store.getState().currentPipeline).toEqual(
  //         {
  //           ...mockPipelines[2],
  //           isInputReadOnly: false
  //         }
  //       )
  //       expect(store.getState().selectedContract).toEqual(
  //         mockPipelines[2].contracts[0]
  //       )
  //     })
  // })

  // it('should dispatch a publish contract action and save response in the redux store', () => {
  //   const contract = mockPipelines[0].contracts[0]

  //   nock('http://localhost')
  //     .post(`/api/contracts/${contract.id}/publish/`)
  //     .reply(200, contract)

  //   expect(typeof publishContract(contract.id)).toEqual('object')

  //   store.dispatch(selectContract(contract.pipeline, contract.id))
  //   return store.dispatch(publishContract(contract.id))
  //     .then(() => {
  //       expect(store.getState().publishSuccess).toEqual(true)
  //       expect(store.getState().publishError).toEqual(null)
  //     })
  // })

  // it('should dispatch a wrong publish contract action and save response in the redux store', () => {
  //   const returnedData = {
  //     error: ['error 1']
  //   }

  //   nock('http://localhost')
  //     .post('/api/contracts/100/publish/')
  //     .reply(400, returnedData)

  //   return store.dispatch(publishContract(100))
  //     .then(() => {
  //       expect(store.getState().publishError).toEqual(returnedData)
  //       expect(store.getState().publishSuccess).toEqual(null)
  //     })
  // })
})
