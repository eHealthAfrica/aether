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

// Combines types, actions and reducers for a specific
// module in one file for easy redux management

import { generateGUID, replaceItemInList, removeItemFromList } from '../utils'
import {
  PIPELINES_URL,
  CONTRACTS_URL,
  PIPELINE_SECTION_INPUT,
  CONTRACT_SECTION_ENTITY_TYPES,
  CONTRACT_SECTION_MAPPING
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
  PIPELINE_DELETE: 'pipeline.delete',

  CONTRACT_NEW: 'contract.new',
  CONTRACT_ADD: 'contract.add',
  CONTRACT_UPDATE: 'contract.update',
  CONTRACT_DELETE: 'contract.delete',

  CONTRACT_PUBLISH_PREFLIGHT: 'contract.publish.preflight',
  CONTRACT_PUBLISH_SUCCESS: 'contract.publish.success',
  CONTRACT_PUBLISH_ERROR: 'contract.publish.error'
}

const ACTIONS_INITIAL_STATE = {
  error: null,
  publishError: null,
  publishState: null,
  publishSuccess: false,
  deleteStatus: null
}

export const INITIAL_STATE = {
  ...ACTIONS_INITIAL_STATE,

  pipelinesList: null,

  currentSection: null,
  currentPipeline: null,
  currentContract: null,
  newContract: null
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

export const selectContract = (pid, cid, section = null) => ({
  type: types.CONTRACT_SELECT,
  payload: { pipeline: pid, contract: cid, section }
})

export const selectSection = (section) => ({
  type: types.SECTION_SELECT,
  payload: section
})

export const startNewContract = (pid = null) => ({
  type: types.CONTRACT_NEW,
  payload: pid
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

export const deletePipeline = (id, opts) => ({
  types: ['', types.PIPELINE_DELETE, types.REQUEST_ERROR],
  promise: client => client.post(
    `${PIPELINES_URL}${id}/delete-artefacts/`,
    { 'Content-Type': 'application/json' },
    { data: opts }
  )
})

export const renamePipeline = (pipelineId, name) => ({
  types: ['', types.PIPELINE_UPDATE, types.REQUEST_ERROR],
  promise: client => client.put(
    `${PIPELINES_URL}${pipelineId}/rename/`,
    { 'Content-Type': 'application/json' },
    { data: { name } }
  )
})

export const addContract = (contract) => ({
  types: ['', types.CONTRACT_ADD, types.REQUEST_ERROR],
  promise: client => client.post(
    `${CONTRACTS_URL}`,
    { 'Content-Type': 'application/json' },
    { data: contract })
})

export const updateContract = (contract) => ({
  types: ['', types.CONTRACT_UPDATE, types.REQUEST_ERROR],
  promise: client => client.put(
    `${CONTRACTS_URL}${contract.id}/`,
    { 'Content-Type': 'application/json' },
    { data: contract })
})

export const deleteContract = (id, opts) => ({
  types: ['', types.CONTRACT_DELETE, types.REQUEST_ERROR],
  promise: client => client.post(
    `${CONTRACTS_URL}${id}/delete-artefacts/`,
    { 'Content-Type': 'application/json' },
    { data: opts }
  )
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
    isInputReadOnly: pipeline.is_read_only,
    contracts: (pipeline.contracts || []).map(parseContract)
  }
}

const parseContract = (contract) => {
  const COLORS = 10 // This value is the number of colors in the `_color-codes.scss`
  // will highlight the relations among mapping rules, entity types and input schema
  const highlightSource = {}
  const highlightDestination = {}

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

    highlightSource[rule.source] = color
    highlightDestination[rule.destination] = color
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

const generateNewContractName = (contracts) => {
  let count = 0
  let newContractName = `Contract ${count}`

  do {
    if (!contracts.find(c => c.name === newContractName)) {
      return newContractName
    }
    count++
    newContractName = `Contract ${count}`
  } while (true)
}

const createNewContractSkeleton = (pipeline) => {
  return {
    id: generateGUID(),
    name: generateNewContractName(pipeline.contracts),
    pipeline: pipeline.id
  }
}

const reducer = (state = INITIAL_STATE, action) => {
  const nextState = { ...state, ...ACTIONS_INITIAL_STATE }

  switch (action.type) {
    case types.REQUEST_ALL: {
      return {
        ...nextState,
        pipelinesList: action.payload.map(parsePipeline)
      }
    }

    case types.PIPELINE_BY_ID: {
      const currentPipeline = parsePipeline(action.payload)
      const currentContract = findContract(currentPipeline, state.currentContract && state.currentContract.id)

      return {
        ...nextState,
        pipelinesList: replaceItemInList(state.pipelinesList, currentPipeline),
        currentPipeline,
        currentContract
      }
    }

    // SELECTION

    case types.CLEAR_SELECTION: {
      return {
        ...nextState,
        currentSection: null,
        currentPipeline: null,
        currentContract: null,
        newContract: null
      }
    }

    case types.PIPELINE_SELECT: {
      const currentPipeline = (state.pipelinesList || []).find(p => p.id === action.payload)
      const currentContract = findContract(currentPipeline, state.currentContract && state.currentContract.id)

      return {
        ...nextState,
        currentSection: PIPELINE_SECTION_INPUT,
        currentPipeline,
        currentContract,
        newContract: null
      }
    }

    case types.CONTRACT_SELECT: {
      const currentPipeline = (state.pipelinesList || [])
        .find(p => p.id === action.payload.pipeline) || state.currentPipeline
      const currentContract = findContract(currentPipeline, action.payload.contract)
      const currentSection = action.payload.section
        ? action.payload.section
        : !state.currentSection || state.currentSection === PIPELINE_SECTION_INPUT
          ? CONTRACT_SECTION_ENTITY_TYPES
          : state.currentSection

      return {
        ...nextState,
        currentSection,
        currentPipeline,
        currentContract,
        newContract: null
      }
    }

    case types.SECTION_SELECT: {
      return {
        ...nextState,
        currentSection: action.payload
      }
    }

    // CHANGES

    case types.PIPELINE_ADD: {
      const newPipeline = parsePipeline(action.payload)

      return {
        ...nextState,
        pipelinesList: [newPipeline, ...(state.pipelinesList || [])],

        currentSection: PIPELINE_SECTION_INPUT,
        currentPipeline: newPipeline
      }
    }

    case types.PIPELINE_UPDATE: {
      const currentPipeline = parsePipeline(action.payload)
      const currentContract = findContract(currentPipeline, state.currentContract && state.currentContract.id)

      return {
        ...nextState,
        pipelinesList: replaceItemInList(state.pipelinesList, currentPipeline),
        currentPipeline,
        currentContract,
        newContract: null
      }
    }

    case types.PIPELINE_DELETE: {
      return {
        ...nextState,
        pipelinesList: removeItemFromList(state.pipelinesList, state.currentPipeline),
        currentPipeline: null,
        currentContract: null,
        newContract: null,
        deleteStatus: action.payload
      }
    }

    case types.CONTRACT_NEW: {
      const currentPipeline = action.payload
        ? (state.pipelinesList || []).find(p => p.id === action.payload) || state.currentPipeline
        : state.currentPipeline
      const newContract = createNewContractSkeleton(currentPipeline)

      return {
        ...nextState,
        currentPipeline,
        newContract,
        currentSection: CONTRACT_SECTION_ENTITY_TYPES
      }
    }

    case types.CONTRACT_ADD: {
      const currentContract = parseContract(action.payload)
      const currentPipeline = (state.pipelinesList || [])
        .find(p => p.id === currentContract.pipeline) || state.currentPipeline
      currentPipeline.contracts = [currentContract, ...currentPipeline.contracts]

      return {
        ...nextState,
        pipelinesList: replaceItemInList(state.pipelinesList, currentPipeline),
        currentPipeline,
        currentContract,
        newContract: null,
        currentSection: currentContract.is_identity ? CONTRACT_SECTION_MAPPING : CONTRACT_SECTION_ENTITY_TYPES
      }
    }

    case types.CONTRACT_UPDATE: {
      const currentContract = parseContract(action.payload)
      const currentPipeline = { ...state.currentPipeline }
      currentPipeline.contracts = replaceItemInList(state.currentPipeline.contracts, currentContract)

      return {
        ...state,
        pipelinesList: replaceItemInList(state.pipelinesList, currentPipeline),
        currentPipeline,
        currentContract
      }
    }

    case types.CONTRACT_DELETE: {
      const currentPipeline = { ...state.currentPipeline }
      currentPipeline.contracts = removeItemFromList(state.currentPipeline.contracts, state.currentContract)
      const currentContract = currentPipeline.contracts.length ? currentPipeline.contracts[0] : null

      return {
        ...state,
        pipelinesList: replaceItemInList(state.pipelinesList, currentPipeline),
        currentPipeline,
        currentContract,
        deleteStatus: action.payload,
        currentSection: currentContract ? CONTRACT_SECTION_ENTITY_TYPES : PIPELINE_SECTION_INPUT
      }
    }

    case types.CONTRACT_PUBLISH_SUCCESS: {
      const statePipeline = (state.pipelinesList || [])
        .find(p => p.id === action.payload.pipeline) || state.currentPipeline
      const currentContract = parseContract(action.payload)
      const currentPipeline = {
        ...statePipeline,
        contracts: replaceItemInList(statePipeline.contracts, currentContract)
      }

      return {
        ...nextState,
        publishSuccess: (action.type === types.CONTRACT_PUBLISH_SUCCESS),
        pipelinesList: replaceItemInList(state.pipelinesList, currentPipeline),
        currentPipeline,
        currentContract,
        newContract: null
      }
    }

    // PUBLISH

    case types.CONTRACT_PUBLISH_PREFLIGHT: {
      return {
        ...nextState,
        publishState: action.payload
      }
    }

    // ERRORS ******************************************************************

    case types.REQUEST_ERROR: {
      return { ...nextState, error: action.error }
    }

    case types.PIPELINE_NOT_FOUND: {
      return {
        ...nextState,
        error: action.error,
        currentPipeline: null,
        currentContract: null
      }
    }

    case types.CONTRACT_PUBLISH_ERROR: {
      return {
        ...nextState,
        publishError: (action.error.error || action.error.message || action.error)
      }
    }

    default:
      return state
  }
}

export default reducer
