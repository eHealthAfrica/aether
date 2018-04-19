// Combines types, actions and reducers for a specific
// module in one file for easy redux management

import { clone } from '../utils'

const types = {
  PIPELINE_ADD: 'pipeline_add',
  PIPELINE_UPDATE: 'pipeline_update',

  PIPELINE_LIST_CHANGED: 'pipeline_list_changed',
  SELECTED_PIPELINE_CHANGED: 'selected_pipeline_changed'
}

const INITIAL_PIPELINE = {
  pipelineList: [],
  selectedPipeline: null
}

export const addPipeline = newPipeline => ({
  // TODO: Change 3rd param to action on request failure when ui endpoints are available
  // types: ['', types.PIPELINE_ADD, types.PIPELINE_ADD],
  // promise: client => client.post(urls.PIPELINE_URL, 'application/x-www-form-urlencoded', {
  //   data: newPipeline
  // })
  type: types.PIPELINE_ADD,
  payload: newPipeline
})

export const updatePipeline = updatedPipeline => ({
  type: types.PIPELINE_UPDATE,
  payload: updatedPipeline
})

export const selectedPipelineChanged = selectedPipeline => ({
  type: types.SELECTED_PIPELINE_CHANGED,
  payload: selectedPipeline
})

const reducer = (state = INITIAL_PIPELINE, action = {}) => {
  const newPipelineList = clone(state.pipelineList)

  switch (action.type) {
    case types.PIPELINE_ADD: {
      const newPipeline = clone(action.payload)
      newPipelineList.unshift(newPipeline)

      return { ...state, pipelineList: newPipelineList, selectedPipeline: newPipeline }
    }

    case types.PIPELINE_UPDATE: {
      const updatedPipeline = clone({ ...state.selectedPipeline, ...action.payload })
      const index = newPipelineList.findIndex(x => x.id === updatedPipeline.id)
      newPipelineList[index] = updatedPipeline

      return { ...state, pipelineList: newPipelineList, selectedPipeline: updatedPipeline }
    }

    case types.SELECTED_PIPELINE_CHANGED: {
      return { ...state, selectedPipeline: clone(action.payload) }
    }

    default:
      return state
  }
}

export default reducer
