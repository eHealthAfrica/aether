import { getSurveysPath } from './utils/paths'

// Include this to enable HMR for this module
if (module.hot) {
  module.hot.accept()
}

/*
This is the home app -> skip welcome screen and go straight to list of surveys
*/

window.location = getSurveysPath({})
