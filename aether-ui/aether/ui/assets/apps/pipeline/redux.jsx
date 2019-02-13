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
  CONTRACT_ADD_FIRST: 'contract_add_first',
  CONTRACT_UPDATE: 'contract_update',
  SELECTED_CONTRACT_CHANGED: 'selected_contract_changed'
}

export const INITIAL_PIPELINE = {
  pipelineList: [],
  selectedPipeline: null,
  selectedContract: null,
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

export const getPipelineById = (pid, cid = null) => {
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
      `${urls.PIPELINES_URL}${pipeline.id}/`,
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

export const selectedContractChanged = selectedContract => ({
  type: types.SELECTED_CONTRACT_CHANGED,
  payload: selectedContract
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

export const updateContract = contract => ({
  types: ['', types.CONTRACT_UPDATE, types.CONTRACT_ERROR],
  promise: client => client.put(
    `${urls.CONTRACTS_URL}${contract.id}/`,
    { 'Content-Type': 'application/json' },
    { data: contract })
})

export const addInitialContract = ({ name, pipeline }) => ({
  types: ['', types.CONTRACT_ADD_FIRST, types.CONTRACT_ERROR],
  promise: client => client.post(
    `${urls.CONTRACTS_URL}`,
    { 'Content-Type': 'application/json' },
    { data: { name, pipeline, is_active: false } })
})

const parsePipeline = pipeline => {
  return { ...pipeline, contracts: pipeline.contracts.map(contract => (parseContract(contract))) }
}

const parseContract = (contract) => {
  const COLORS = 10 // This value is the number of colors in the `_color-codes.scss`
  // will highlight the relations among mapping rules, entity types and input schema
  const highlightSource = {}
  const highlightDestination = []

  // each EntityType has a color based on the order it was added to the list
  const entityColors = {}
  const entityTypes = (contract.entity_types || [])
  entityTypes.forEach((entity, index) => {
    entityColors[entity.name] = (index % COLORS) + 1
  })

  // indicate the color to each JSON path in each rule source and destination
  const mappingRules = (contract.mapping || [])
  mappingRules.forEach(rule => {
    // find out the number assigned to the linked Entity Type
    const entityType = rule.destination.split('.')[0]
    const color = entityColors[entityType] || 0

    highlightSource[rule.source.replace('$.', '')] = color
    highlightDestination.push(rule.destination)
  })

  return {
    ...clone(contract),
    highlightSource,
    highlightDestination
  }
}

const checkReadOnlyPipelines = pipelines => {
  if (pipelines && pipelines.length) {
    pipelines.forEach(pipeline => {
      pipeline = checkReadOnlySinglePipeline(pipeline)
      pipeline = parsePipeline(pipeline)
    })
  }
  return pipelines
}

const checkReadOnlySinglePipeline = pipeline => {
  const readOnlyMappings = pipeline.contracts.filter(x => (x.is_read_only))
  let isInputReadOnly = false
  if (readOnlyMappings.length) {
    isInputReadOnly = true
  }
  pipeline.isInputReadOnly = isInputReadOnly
  return pipeline
}

const reducer = (state = INITIAL_PIPELINE, action) => {
  const newPipelineList = clone(state.pipelineList)
  state = { ...state, publishError: null, publishSuccess: null, isNewPipeline: false, error: null }
  switch (action.type) {
    case types.PIPELINE_ADD: {
      const newPipeline = parsePipeline(action.payload)
      return { ...state, pipelineList: [newPipeline, ...newPipelineList], selectedPipeline: newPipeline, isNewPipeline: true }
    }

    case types.PIPELINE_BY_ID: {
      const returnedPipeline = parsePipeline(action.payload)
      const index = newPipelineList.findIndex(x => x.id === returnedPipeline.id)
      let currentContract = null
      if (returnedPipeline.contracts && returnedPipeline.contracts.length) {
        if (currentContractId) {
          currentContract = returnedPipeline.contracts.find(x => x.id === currentContractId)
        }
        if (!currentContract) {
          currentContract = returnedPipeline.contracts[0]
        }
      }
      newPipelineList[index] = returnedPipeline
      return { ...state, pipelineList: newPipelineList, selectedPipeline: checkReadOnlySinglePipeline(returnedPipeline), selectedContract: currentContract }
    }

    case types.CONTRACT_UPDATE: {
      const returnedContract = parseContract(action.payload)
      const index = state.selectedPipeline.contracts.findIndex(x => x.id === returnedContract.id)
      const uPipeline = { ...state.selectedPipeline }
      uPipeline.contracts[index] = returnedContract
      const pIndex = newPipelineList.findIndex(x => x.id === state.selectedPipeline.id)
      newPipelineList[pIndex] = uPipeline
      return { ...state, pipelineList: newPipelineList, selectedPipeline: uPipeline, selectedContract: returnedContract }
    }

    case types.SELECTED_PIPELINE_CHANGED: {
      return { ...state, selectedPipeline: parsePipeline(checkReadOnlySinglePipeline(action.payload)) }
    }

    case types.SELECTED_CONTRACT_CHANGED: {
      return { ...state, selectedContract: parseContract(action.payload) }
    }

    case types.GET_ALL: {
      return { ...state, pipelineList: checkReadOnlyPipelines(action.payload) }
    }

    case types.PIPELINE_ERROR: {
      return { ...state, error: action.error }
    }

    case types.PIPELINE_NOT_FOUND: {
      return { ...state, notFound: action.error, selectedPipeline: null }
    }

    case types.PIPELINE_PUBLISH_ERROR: {
      return { ...state, publishError: action.error.error || action.error.message || action.error }
    }

    case types.PIPELINE_PUBLISH_SUCCESS: {
      const updatedPipeline = parsePipeline(checkReadOnlySinglePipeline(action.payload))
      const currentContract = updatedPipeline.contracts.find(x => x.id === state.selectedContract.id)
      const index = newPipelineList.findIndex(x => x.id === updatedPipeline.id)
      newPipelineList[index] = updatedPipeline
      return {
        ...state,
        pipelineList: newPipelineList,
        selectedPipeline: updatedPipeline,
        publishSuccess: true,
        selectedContract: currentContract
      }
    }

    case types.GET_FROM_KERNEL: {
      return { ...state, pipelineList: checkReadOnlyPipelines(action.payload) }
    }

    case types.CONTRACT_ADD_FIRST: {
      const index = newPipelineList.findIndex(x => x.id === action.payload.pipeline)
      let pipeline = { ...newPipelineList[index] }
      if (pipeline) {
        const pContract = parseContract(action.payload)
        pipeline.contracts = [pContract, ...pipeline.contracts]
        const processedPipeline = checkReadOnlySinglePipeline(pipeline)
        newPipelineList[index] = processedPipeline
        return {
          ...state,
          pipelineList: newPipelineList,
          selectedPipeline: processedPipeline,
          selectedContract: pContract,
          isNewPipeline: true
        }
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
