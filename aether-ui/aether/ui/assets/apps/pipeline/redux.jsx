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
  PIPELINE_PUBLISH_SUCCESS: 'pipeline_publish_success',
  PIPELINE_PUBLISH_ERROR: 'pipeline_publish_error',
  PIPELINE_LIST_CHANGED: 'pipeline_list_changed',
  SELECTED_PIPELINE_CHANGED: 'selected_pipeline_changed',
  GET_ALL: 'pipeline_get_all',
  PIPELINE_ERROR: 'pipeline_error',
  GET_BY_ID: 'pipeline_get_by_id',
  PIPELINE_NOT_FOUND: 'pipeline_not_found',
  GET_FROM_KERNEL: 'get_from_kernel',
  GET_FROM_KERNEL_ERROR: 'get_from_kernel_error'
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

export const addPipeline = ({ name }) => ({
  types: ['', types.PIPELINE_ADD, types.PIPELINE_ERROR],
  promise: client => client.post(
    `${urls.PIPELINES_URL}`,
    { 'Content-Type': 'application/json' },
    { data: { name } })
})

export const getPipelineById = id => ({
  types: ['', types.PIPELINE_UPDATE, types.PIPELINE_NOT_FOUND],
  promise: client => client.get(
    `${urls.PIPELINES_URL}${id}/`,
    { 'Content-Type': 'application/json' }
  )
})

export const updatePipeline = pipeline => ({
  types: ['', types.PIPELINE_UPDATE, types.PIPELINE_ERROR],
  promise: client => client.put(
    `${urls.PIPELINES_URL}${pipeline.id}/`,
    { 'Content-Type': 'application/json' },
    { data: pipeline }
  )
})

export const publishPipeline = (id, projectName = PROJECT_NAME, overwrite = false) => ({
  types: ['', types.PIPELINE_PUBLISH_SUCCESS, types.PIPELINE_PUBLISH_ERROR],
  promise: client => client.post(`${urls.PIPELINES_URL}${id}/publish/`,
    { 'Content-Type': 'application/json' },
    { data: { project_name: projectName, overwrite } }
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

    highlightSource[rule.source] = color
    highlightDestination.push(rule.destination)
  })

  return {
    ...clone(pipeline),
    highlightSource,
    highlightDestination
  }
}

const reducer = (state = INITIAL_PIPELINE, action) => {
  const newPipelineList = clone(state.pipelineList)
  state = { ...state, publishError: null, publishSuccess: null, isNewPipeline: false, error: null }
  switch (action.type) {
    case types.PIPELINE_ADD: {
      const newPipeline = parsePipeline(action.payload)
      return { ...state, pipelineList: [newPipeline, ...newPipelineList], selectedPipeline: newPipeline, isNewPipeline: true }
    }

    case types.PIPELINE_UPDATE: {
      const updatedPipeline = parsePipeline({ ...state.selectedPipeline, ...action.payload })
      const index = newPipelineList.findIndex(x => x.id === updatedPipeline.id)
      newPipelineList[index] = updatedPipeline

      return { ...state, pipelineList: newPipelineList, selectedPipeline: updatedPipeline }
    }

    case types.SELECTED_PIPELINE_CHANGED: {
      return { ...state, selectedPipeline: parsePipeline(action.payload) }
    }

    case types.GET_ALL: {
      return { ...state, pipelineList: action.payload.results || [] }
    }

    case types.PIPELINE_ERROR: {
      return { ...state, error: action.error }
    }

    case types.PIPELINE_NOT_FOUND: {
      return { ...state, notFound: action.error, selectedPipeline: null }
    }

    case types.PIPELINE_PUBLISH_SUCCESS: {
      if (action.payload.pipeline) {
        const updatedPipeline = parsePipeline({ ...state.selectedPipeline, ...action.payload.pipeline })
        const index = newPipelineList.findIndex(x => x.id === action.payload.pipeline.id)
        newPipelineList[index] = updatedPipeline
        return { ...state, publishSuccess: action.payload.successful, pipelineList: newPipelineList, selectedPipeline: updatedPipeline }
      }
      return { ...state, publishSuccess: action.payload.successful }
    }

    case types.PIPELINE_PUBLISH_ERROR: {
      return { ...state, publishError: action.error.error }
    }

    case types.GET_FROM_KERNEL: {
      return { ...state, pipelineList: action.payload }
    }

    default:
      return state
  }
}

export default reducer
