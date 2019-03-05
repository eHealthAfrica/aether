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

import { replaceItemInList } from '../utils'
import {
  PIPELINES_URL,
  CONTRACTS_URL,
  PIPELINE_SECTION_INPUT,
  CONTRACT_SECTION_ENTITY_TYPES,
  CONTRACT_SECTION_SETTINGS
} from '../utils/constants'

export const types = {
  REQUEST_ALL: 'request.all',
  REQUEST_ERROR: 'request.error',

  PIPELINE_BY_ID: 'pipeline.by_id',
  PIPELINE_NOT_FOUND: 'pipeline.not_found',

  CLEAR_SELECTION: 'pipeline.selected.none',
  PIPELINE_SELECT: 'pipeline.select',
  CONTRACT_SELECT: 'contract.select',
  SECTION_SELECT: 'section.select',

  PIPELINE_ADD: 'pipeline.add',
  PIPELINE_UPDATE: 'pipeline.update',

  CONTRACT_ADD: 'contract.add',
  CONTRACT_UPDATE: 'contract.update',

  CONTRACT_PUBLISH_PREFLIGHT: 'contract.publish.preflight',
  CONTRACT_PUBLISH_SUCCESS: 'contract.publish.success',
  CONTRACT_PUBLISH_ERROR: 'contract.publish.error'
}

export const INITIAL_STATE = {
  pipelineList: [],

  currentSection: null,
  currentPipeline: null,
  currentContract: null,

  error: null,

  publishError: null,
  publishState: null,
  publishSuccess: false
}

export const getPipelines = () => ({
  types: ['', types.REQUEST_ALL, types.REQUEST_ERROR],
  promise: client => client.post(
    `${PIPELINES_URL}fetch/`,
    { 'Content-Type': 'application/json' }
  )
})

export const clearSelection = () => ({
  type: types.CLEAR_SELECTION
})

export const selectPipeline = (pid) => ({
  type: types.PIPELINE_SELECT,
  payload: pid
})

export const selectContract = (pid, cid) => ({
  type: types.CONTRACT_SELECT,
  payload: { pipeline: pid, contract: cid }
})

export const selectSection = (section) => ({
  type: types.SECTION_SELECT,
  payload: section
})

export const getPipelineById = (pid) => {
  return {
    types: ['', types.PIPELINE_BY_ID, types.PIPELINE_NOT_FOUND],
    promise: client => client.get(
      `${PIPELINES_URL}${pid}/`,
      { 'Content-Type': 'application/json' }
    )
  }
}

export const addPipeline = ({ name }) => ({
  types: ['', types.PIPELINE_ADD, types.REQUEST_ERROR],
  promise: client => client.post(
    `${PIPELINES_URL}`,
    { 'Content-Type': 'application/json' },
    { data: { name } })
})

export const updatePipeline = (pipeline) => {
  return {
    types: ['', types.PIPELINE_UPDATE, types.REQUEST_ERROR],
    promise: client => client.put(
      `${PIPELINES_URL}${pipeline.id}/`,
      { 'Content-Type': 'application/json' },
      { data: pipeline }
    )
  }
}

export const addContract = (pipeline) => ({
  types: ['', types.CONTRACT_ADD, types.REQUEST_ERROR],
  promise: client => client.post(
    `${CONTRACTS_URL}`,
    { 'Content-Type': 'application/json' },
    { data: { name: generateNewContractName(pipeline), pipeline: pipeline.id } })
})

export const updateContract = (contract) => ({
  types: ['', types.CONTRACT_UPDATE, types.REQUEST_ERROR],
  promise: client => client.put(
    `${CONTRACTS_URL}${contract.id}/`,
    { 'Content-Type': 'application/json' },
    { data: contract })
})

export const publishPreflightContract = (cid) => ({
  types: ['', types.CONTRACT_PUBLISH_PREFLIGHT, types.CONTRACT_PUBLISH_ERROR],
  promise: client => client.get(
    `${CONTRACTS_URL}${cid}/publish-preflight/`,
    { 'Content-Type': 'application/json' }
  )
})

export const publishContract = (cid) => ({
  types: ['', types.CONTRACT_PUBLISH_SUCCESS, types.CONTRACT_PUBLISH_ERROR],
  promise: client => client.post(
    `${CONTRACTS_URL}${cid}/publish/`,
    { 'Content-Type': 'application/json' }
  )
})

const parsePipeline = (pipeline) => {
  return {
    ...pipeline,
    isInputReadOnly: (pipeline.contracts.filter(c => (c.is_read_only)).length > 0),
    contracts: pipeline.contracts.map(parseContract)
  }
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
  const mappingRules = (contract.mapping_rules || [])
  mappingRules.forEach(rule => {
    // find out the number assigned to the linked Entity Type
    const entityType = rule.destination.split('.')[0]
    const color = entityColors[entityType] || 0

    highlightSource[rule.source.replace('$.', '')] = color
    highlightDestination.push(rule.destination)
  })

  return {
    ...contract,
    highlightSource,
    highlightDestination
  }
}

const findContract = (pipeline, cid) => {
  let contract = null
  if (pipeline && pipeline.contracts) {
    if (cid) {
      contract = pipeline.contracts.find(c => c.id === cid)
    }
    if (!contract) {
      contract = pipeline.contracts[0]
    }
  }
  return contract
}

const generateNewContractName = (pipeline) => {
  let count = 0
  let newContractName = pipeline.name

  do {
    if (!pipeline.contracts.find(c => c.name === newContractName)) {
      return newContractName
    }

    newContractName = `Contract ${count}`
    count++
  } while (true)
}

const reducer = (state = INITIAL_STATE, action) => {
  state = {
    ...state,
    // clean previous state changes
    error: null,
    publishError: null,
    publishState: null,
    publishSuccess: false
  }

  switch (action.type) {
    case types.REQUEST_ALL: {
      return {
        ...state,
        pipelineList: action.payload.map(parsePipeline)
      }
    }

    case types.PIPELINE_BY_ID: {
      const currentPipeline = parsePipeline(action.payload)
      const currentContract = findContract(currentPipeline, state.currentContract && state.currentContract.id)

      return {
        ...state,
        pipelineList: replaceItemInList(state.pipelineList, currentPipeline),
        currentPipeline,
        currentContract
      }
    }

    // SELECTION

    case types.CLEAR_SELECTION: {
      return {
        ...state,
        currentSection: null,
        currentPipeline: null,
        currentContract: null
      }
    }

    case types.PIPELINE_SELECT: {
      const currentPipeline = state.pipelineList.find(p => p.id === action.payload)
      const currentContract = findContract(currentPipeline, state.currentContract && state.currentContract.id)

      return {
        ...state,
        currentSection: PIPELINE_SECTION_INPUT,
        currentPipeline,
        currentContract
      }
    }

    case types.CONTRACT_SELECT: {
      const currentPipeline = state.pipelineList.find(p => p.id === action.payload.pipeline) || state.currentPipeline
      const currentContract = findContract(currentPipeline, action.payload.contract)
      const currentSection = !state.currentSection || state.currentSection === PIPELINE_SECTION_INPUT
        ? CONTRACT_SECTION_ENTITY_TYPES
        : state.currentSection

      return {
        ...state,
        currentSection,
        currentPipeline,
        currentContract
      }
    }

    case types.SECTION_SELECT: {
      return {
        ...state,
        currentSection: action.payload
      }
    }

    // CHANGES

    case types.PIPELINE_ADD: {
      const newPipeline = parsePipeline(action.payload)

      return {
        ...state,
        pipelineList: [ newPipeline, ...state.pipelineList ],

        currentSection: PIPELINE_SECTION_INPUT,
        currentPipeline: newPipeline,
        currentContract: newPipeline.contracts[0]
      }
    }

    case types.PIPELINE_UPDATE: {
      const currentPipeline = parsePipeline(action.payload)
      const currentContract = findContract(currentPipeline, state.currentContract && state.currentContract.id)

      return {
        ...state,
        pipelineList: replaceItemInList(state.pipelineList, currentPipeline),
        currentPipeline,
        currentContract
      }
    }

    case types.CONTRACT_ADD: {
      const currentContract = parseContract(action.payload)
      const currentPipeline = state.pipelineList.find(p => p.id === currentContract.pipeline) || state.currentPipeline
      currentPipeline.contracts = [ currentContract, ...currentPipeline.contracts ]

      return {
        ...state,
        pipelineList: replaceItemInList(state.pipelineList, currentPipeline),

        currentSection: CONTRACT_SECTION_SETTINGS,
        currentPipeline,
        currentContract
      }
    }

    case types.CONTRACT_UPDATE:
    case types.CONTRACT_PUBLISH_SUCCESS: {
      const currentContract = parseContract(action.payload)
      const currentPipeline = {
        ...state.currentPipeline,
        contracts: replaceItemInList(state.currentPipeline.contracts, currentContract)
      }

      return {
        ...state,
        publishSuccess: (action.type === types.CONTRACT_PUBLISH_SUCCESS),
        currentPipeline,
        currentContract
      }
    }

    // PUBLISH

    case types.CONTRACT_PUBLISH_PREFLIGHT: {
      return {
        ...state,
        publishState: action.payload
      }
    }

    // ERRORS ******************************************************************

    case types.REQUEST_ERROR: {
      return { ...state, error: action.error }
    }

    case types.PIPELINE_NOT_FOUND: {
      return {
        ...state,
        error: action.error,
        currentPipeline: null,
        currentContract: null
      }
    }

    case types.CONTRACT_PUBLISH_ERROR: {
      return {
        ...state,
        publishError: (action.error.error || action.error.message || action.error)
      }
    }

    default:
      return state
  }
}

export default reducer
