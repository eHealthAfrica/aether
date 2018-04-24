// Combines types, actions and reducers for a specific
// module in one file for easy redux management

import { clone } from '../utils'
import urls from '../utils/urls'
import ApiClient from '../utils/api';

export const types = {
  PIPELINE_ADD: 'pipeline_add',
  PIPELINE_UPDATE: 'pipeline_update',

  PIPELINE_LIST_CHANGED: 'pipeline_list_changed',
  SELECTED_PIPELINE_CHANGED: 'selected_pipeline_changed',
  GET_ALL: 'pipeline_get_all',
  PIPELINE_ERROR: 'pipeline_error',
  GET_BY_ID: 'pipeline_get_by_id'
}

export const INITIAL_PIPELINE = {
  pipelineList: [],
  selectedPipeline: null,
  error: null
}

export const addPipeline = newPipeline => dispatch => {
  const client = new ApiClient()
  client.post(
    urls.PIPELINES_URL,
    { 'Content-Type': 'application/json' },
    { data: {name: newPipeline.name} }
  )
  .then(res => {
    dispatch({
      type: types.PIPELINE_ADD,
      payload: res
    })
  })
  .catch(error => {
    dispatch({
      type: types.PIPELINE_ERROR,
      payload: error
    })
  })
}

export const getPipelineById = id => ({
  type: types.GET_BY_ID,
  payload: id
})

export const updatePipeline = pipeline => dispatch => {
  const client = new ApiClient()
  client.put(
    `${urls.PIPELINES_URL}${pipeline.id}/`,
    { 'Content-Type': 'application/json' },
    { data: pipeline }
  )
  .then(res => {
    dispatch({
      type: types.PIPELINE_UPDATE,
      payload: res
    })
  })
  .catch(error => {
    dispatch({
      type: types.PIPELINE_ERROR,
      payload: error
    })
  })
}

export const selectedPipelineChanged = selectedPipeline => ({
  type: types.SELECTED_PIPELINE_CHANGED,
  payload: selectedPipeline
})

export const getPipelines = () => ({
  types: ['', types.GET_ALL, types.PIPELINE_ERROR],
  promise: client => client.get(`${urls.PIPELINES_URL}?limit=5000`, { 'Content-Type': 'application/json' }) // limit query_string used instead of pagination (temporary)
})

const reducer = (state = INITIAL_PIPELINE, action = {}) => {
  const newPipelineList = clone(state.pipelineList)

  switch (action.type) {
    case types.PIPELINE_ADD: {
      const newPipeline = clone(action.payload)
      newPipelineList.unshift(newPipeline)

      return { ...state, pipelineList: newPipelineList, selectedPipeline: newPipeline, error: null }
    }

    case types.PIPELINE_UPDATE: {
      const updatedPipeline = clone({ ...state.selectedPipeline, ...action.payload })
      const index = newPipelineList.findIndex(x => x.id === updatedPipeline.id)
      newPipelineList[index] = updatedPipeline

      return { ...state, pipelineList: newPipelineList, selectedPipeline: updatedPipeline, error: null }
    }

    case types.SELECTED_PIPELINE_CHANGED: {
      return { ...state, selectedPipeline: clone(action.payload), error: null }
    }

    case types.GET_ALL: {
      return { ...state, pipelineList: action.payload.results || [], error: null }
    }

    case types.PIPELINE_ERROR: {
      return { ...state, error: action.error }
    }

    case types.GET_BY_ID: {
      let foundPipeline = state.pipelineList.filter(pipeline => (pipeline.id === action.payload))
      foundPipeline = foundPipeline.length && foundPipeline[0]
      return { ...state, selectedPipeline: foundPipeline, error: null }
    }

    default:
      return state
  }
}

export default reducer
