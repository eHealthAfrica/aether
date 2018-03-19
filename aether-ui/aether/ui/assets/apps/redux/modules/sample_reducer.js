// Combines types, actions and reducers for a specific 
// module in one file for easy redux management

import { combineReducers } from 'redux';
import urls from '../../utils/urls';
import { cloneDeep } from 'lodash';

const types = {
  SAMPLE_TYPE: 'sample_type'
};

const sampleAction = () => ({
  types: ['', types.SAMPLE_TYPE],
  promise: client => client.get(urls.SAMPLE_URL, 'application/x-www-form-urlencoded')
});

const INITIAL_SAMPLE = {
  sampleList: [{name: 'sample A', id: 1 }, {name: 'sample B', id: 2 }]
};

const sampleReducer = (state = INITIAL_SAMPLE, action) => {
  let newSampleList = cloneDeep(state.sampleList);
  const findIndex = arr => arr.findIndex(x => x.id === action.payload.id);

  switch (action.type) {
    case types.SAMPLE_TYPE: {
      const index = findIndex(newSampleList);
      newSampleList[index] = action.payload;
      return { ...state, sampleList: newSampleList };
    }
    default:
      return state;
  }
};

//Export actions
export const sampleActions = {
  sampleAction
};

export default combineReducers({ sampleReducer });