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

// Combines types, actions and reducers for a specific
// module in one file for easy redux management

import { clone } from '../utils'
import urls from '../utils/urls'
import ApiClient from '../utils/api'
import { PROJECT_NAME, MAX_PAGE_SIZE } from '../utils/constants'

export const types = {
  PIPELINE_ADD: 'pipeline_add',
  PIPELINE_UPDATE: 'pipeline_update',
  PIPELINE_PUBLISH_ERROR: 'pipeline_publish_error',
  PIPELINE_PUBLISH_SUCCESS: 'pipeline_publish_success',
  PIPELINE_LIST_CHANGED: 'pipeline_list_changed',
  SELECTED_PIPELINE_CHANGED: 'selected_pipeline_changed',
  PIPELINE_BY_ID: 'pipeline_by_id',
  GET_ALL: 'pipeline_get_all',
  PIPELINE_ERROR: 'pipeline_error',
  GET_BY_ID: 'pipeline_get_by_id',
  PIPELINE_NOT_FOUND: 'pipeline_not_found',
  GET_FROM_KERNEL: 'get_from_kernel',
  GET_FROM_KERNEL_ERROR: 'get_from_kernel_error',
  CONTRACT_ERROR: 'contract_error',
  CONTRACT_ADD_FIRST: 'contract_add_first'
}

export const INITIAL_PIPELINE = {
  pipelineList: [],
  selectedPipeline: null,
  error: null,
  notFound: null,
  publishError: null,
  publishSuccess: null,
  isNewPipeline: false
}

let currentContractId = null

export const addPipeline = ({ name }) => ({
  types: ['', types.PIPELINE_ADD, types.PIPELINE_ERROR],
  promise: client => client.post(
    `${urls.PIPELINES_URL}`,
    { 'Content-Type': 'application/json' },
    { data: { name } })
})

export const getPipelineById = (pid, cid) => {
  currentContractId = cid
  return {
    types: ['', types.PIPELINE_BY_ID, types.PIPELINE_NOT_FOUND],
    promise: client => client.get(
      `${urls.PIPELINES_URL}${pid}/`,
      { 'Content-Type': 'application/json' }
    )
  }
}

export const updatePipeline = pipeline => {
  currentContractId = pipeline.id
  return {
    types: ['', types.PIPELINE_BY_ID, types.PIPELINE_ERROR],
    promise: client => client.put(
      `${urls.PIPELINES_URL}${pipeline.pipeline}/`,
      { 'Content-Type': 'application/json' },
      { data: pipeline }
    )
  }
}

export const publishPipeline = (pid, cid, projectName = PROJECT_NAME, overwrite = false, ids = {}) => ({
  types: ['', types.PIPELINE_PUBLISH_SUCCESS, types.PIPELINE_PUBLISH_ERROR],
  promise: client => client.post(`${urls.PIPELINES_URL}${pid}/publish/`,
    { 'Content-Type': 'application/json' },
    { data: { project_name: projectName, overwrite, contract_id: cid, ids } }
  )
})

export const selectedPipelineChanged = selectedPipeline => ({
  type: types.SELECTED_PIPELINE_CHANGED,
  payload: selectedPipeline
})

export const getPipelines = () => ({
  types: ['', types.GET_ALL, types.PIPELINE_ERROR],
  promise: client => client.get(
    // limit query_string used instead of pagination (temporary)
    `${urls.PIPELINES_URL}?limit=${MAX_PAGE_SIZE}`,
    { 'Content-Type': 'application/json' }
  )
})

export const fetchPipelines = () => ({
  types: ['', types.GET_FROM_KERNEL, types.GET_FROM_KERNEL_ERROR],
  promise: client => client.post(
    `${urls.PIPELINES_URL}fetch/?limit=${MAX_PAGE_SIZE}`,
    { 'Content-Type': 'application/json' })
})

export const updateContract = pipeline => dispatch => {
  const client = new ApiClient()
  client.put(
    `${urls.CONTRACTS_URL}${pipeline.id}/`,
    { 'Content-Type': 'application/json' },
    { data: pipeline }
  )
    .then(res => {
      contractToPipeline(res, dispatch)
    })
    .catch(err => {
      dispatch({
        type: types.CONTRACT_ERROR,
        error: err
      })
    })
}

export const addInitialContract = ({ name, pipeline }) => ({
  types: ['', types.CONTRACT_ADD_FIRST, types.CONTRACT_ERROR],
  promise: client => client.post(
    `${urls.CONTRACTS_URL}`,
    { 'Content-Type': 'application/json' },
    { data: { name, pipeline, is_active: false } })
})

const parsePipeline = (pipeline) => {
  const COLORS = 10 // This value is the number of colors in the `_color-codes.scss`
  // will highlight the relations among mapping rules, entity types and input schema
  const highlightSource = {}
  const highlightDestination = []

  // each EntityType has a color based on the order it was added to the list
  const entityColors = {}
  const entityTypes = (pipeline.entity_types || [])
  entityTypes.forEach((entity, index) => {
    entityColors[entity.name] = (index % COLORS) + 1
  })

  // indicate the color to each JSON path in each rule source and destination
  const mappingRules = (pipeline.mapping || [])
  mappingRules.forEach(rule => {
    // find out the number assigned to the linked Entity Type
    const entityType = rule.destination.split('.')[0]
    const color = entityColors[entityType] || 0

    highlightSource[rule.source.replace('$.', '')] = color
    highlightDestination.push(rule.destination)
  })

  return {
    ...clone(pipeline),
    highlightSource,
    highlightDestination
  }
}

const pipelineTranslator = (pipeline) => {
  const convertedPipelines = []
  if (pipeline.contracts.length) {
    const readOnlyMappings = pipeline.contracts.filter(x => (x.is_read_only))
    let isInputReadOnly = false
    if (readOnlyMappings.length) {
      isInputReadOnly = true
    }
    pipeline.contracts.map(contract => {
      convertedPipelines.push(
        parsePipeline({
          ...contract,
          pipeline: pipeline.id,
          input: pipeline.input,
          schema: pipeline.schema,
          mappingset: pipeline.mappingset,
          isInputReadOnly
        })
      )
    })
  } else {
    convertedPipelines.push(
      {
        pipeline: pipeline.id,
        mapping_errors: [],
        entity_types: [],
        mapping: [],
        isInputReadOnly: false,
        ...pipeline
      }
    )
  }
  return convertedPipelines
}

const contractToPipeline = (contract, dispatch) => {
  const client = new ApiClient()
  client.get(contract.pipeline_url)
    .then(res => {
      currentContractId = contract.id
      dispatch({
        type: types.PIPELINE_BY_ID,
        payload: res
      })
    })
    .catch(err => {
      dispatch({
        type: types.CONTRACT_ERROR,
        error: err
      })
    })
}

const reducer = (state = INITIAL_PIPELINE, action) => {
  const flattenPipelineContracts = pipelines => {
    let results = []
    if (pipelines && pipelines.length) {
      pipelines.forEach(pipeline => {
        results = [...results, ...pipelineTranslator(pipeline)]
      })
    }
    return results
  }
  const newPipelineList = clone(state.pipelineList)
  state = { ...state, publishError: null, publishSuccess: null, isNewPipeline: false, error: null }
  switch (action.type) {
    case types.PIPELINE_ADD: {
      const newPipeline = pipelineTranslator(action.payload)
      return { ...state, pipelineList: [...newPipeline, ...newPipelineList], selectedPipeline: action.payload, isNewPipeline: true }
    }

    case types.PIPELINE_BY_ID: {
      const gottenPipelines = pipelineTranslator(action.payload)
      const currentPipeline = gottenPipelines.find(x => x.id === currentContractId)
      gottenPipelines.forEach(pipeline => {
        const index = newPipelineList.findIndex(x => x.id === pipeline.id)
        if (index >= 0) {
          newPipelineList[index] = pipeline
        } else {
          newPipelineList.push(pipeline)
        }
      })
      currentContractId = null
      return { ...state, pipelineList: newPipelineList, selectedPipeline: currentPipeline }
    }

    case types.SELECTED_PIPELINE_CHANGED: {
      return { ...state, selectedPipeline: parsePipeline(action.payload) }
    }

    case types.GET_ALL: {
      return { ...state, pipelineList: flattenPipelineContracts(action.payload.results) }
    }

    case types.PIPELINE_ERROR: {
      return { ...state, error: action.error }
    }

    case types.PIPELINE_NOT_FOUND: {
      return { ...state, notFound: action.error, selectedPipeline: null }
    }

    case types.PIPELINE_PUBLISH_ERROR: {
      return { ...state, publishError: action.error.error }
    }

    case types.PIPELINE_PUBLISH_SUCCESS: {
      const updatedPipelines = pipelineTranslator(action.payload)
      const currentPipeline = updatedPipelines.find(x => x.id === state.selectedPipeline.id)
      updatedPipelines.forEach(pipeline => {
        const index = newPipelineList.findIndex(x => x.id === pipeline.id)
        newPipelineList[index] = pipeline
      })
      return { ...state, pipelineList: newPipelineList, selectedPipeline: currentPipeline, publishSuccess: true }
    }

    case types.GET_FROM_KERNEL: {
      return { ...state, pipelineList: flattenPipelineContracts(action.payload) }
    }

    case types.CONTRACT_ADD_FIRST: {
      const index = newPipelineList.findIndex(x => x.id === action.payload.pipeline)
      let pipeline = { ...newPipelineList[index] }
      if (pipeline) {
        pipeline.contracts = [action.payload, ...pipeline.contracts]
        const newPipelines = pipelineTranslator(pipeline)
        const removedInitialPipeline = newPipelineList.filter(e => e !== newPipelineList[index])
        return { ...state, pipelineList: [...newPipelines, ...removedInitialPipeline], selectedPipeline: newPipelines[0] || {}, isNewPipeline: true }
      } else {
        return { ...state, error: 'Could not find a linked pipeline' }
      }
    }

    case types.CONTRACT_ERROR: {
      return { ...state, error: action.error }
    }

    default:
      return state
  }
}

export default reducer
