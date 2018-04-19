// Combines types, actions and reducers for a specific
// module in one file for easy redux management

import { clone } from '../utils'
import urls from '../utils/urls'

export const types = {
  PIPELINE_UPDATE: 'pipeline_update',
  PIPELINE_ADD: 'pipeline_add',
  PIPELINE_LIST_CHANGED: 'pipeline_list_changed',
  SELECTED_PIPELINE_CHANGED: 'selected_pipeline_changed',
  GET_ALL: 'pipeline_get_all',
  GET_ALL_FAILED: 'pipeline_get_all_failed',
  GET_BY_ID: 'pipeline_get_by_id'
}

export const INITIAL_PIPELINE = {
  pipelineList: [],
  selectedPipeline: null,
  error: null
}

export const addPipeline = newPipeline => ({
  type: types.PIPELINE_ADD,
  payload: newPipeline
})

export const getPipelineById = id => ({
  type: types.GET_BY_ID,
  payload: id
})

export const updatePipeline = pipeline => ({
  type: types.PIPELINE_UPDATE,
  payload: pipeline
})

export const selectedPipelineChanged = selectedPipeline => ({
  type: types.SELECTED_PIPELINE_CHANGED,
  payload: selectedPipeline
})

export const getPipelines = () => ({
  types: ['', types.GET_ALL, types.GET_ALL_FAILED],
  promise: client => client.get(urls.MOCK_PIPELINES_URL, { 'Content-Type': 'application/json' })
})

const reducer = (state = INITIAL_PIPELINE, action = {}) => {
  const newPipelineList = clone(state.pipelineList)
  const findIndex = arr => arr.findIndex(x => x.id === action.payload.id)

  switch (action.type) {
    case types.PIPELINE_ADD: {
      newPipelineList.unshift(action.payload)
      return { ...state, pipelineList: newPipelineList }
    }

    case types.PIPELINE_UPDATE: {
      const index = findIndex(newPipelineList)
      newPipelineList[index] = action.payload
      return { ...state, pipelineList: newPipelineList }
    }

    case types.SELECTED_PIPELINE_CHANGED: {
      return { ...state, selectedPipeline: action.payload }
    }

    case types.GET_ALL: {
      return { ...state, pipelineList: action.payload.results || [], error: null }
    }

    case types.GET_ALL_FAILED: {
      return { ...state, error: action.error }
    }

    case types.GET_BY_ID: {
      let foundPipeline = state.pipelineList.filter(pipeline => (pipeline.id === action.payload))
      foundPipeline = foundPipeline.length && foundPipeline[0]
      return { ...state, selectedPipeline: foundPipeline }
    }

    default:
      return state
  }
}

export default reducer
