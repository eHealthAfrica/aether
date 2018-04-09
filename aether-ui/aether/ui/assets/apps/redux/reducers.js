import { combineReducers } from 'redux';
import samples from './modules/sample_reducer';
import pipelines from './modules/pipeline';

export default combineReducers({
  samples,
  pipelines
});