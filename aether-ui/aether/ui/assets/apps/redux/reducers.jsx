import { combineReducers } from 'redux'

import pipelines from '../pipeline/redux'
import constants from '../utils/constants'

export default combineReducers({
  pipelines,
  constants
})
