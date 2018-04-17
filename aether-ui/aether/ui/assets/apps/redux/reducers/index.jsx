import { combineReducers } from 'redux'

import { pipelineReducer } from '../../pipeline/redux'

export default combineReducers({
  pipelines: pipelineReducer
})
