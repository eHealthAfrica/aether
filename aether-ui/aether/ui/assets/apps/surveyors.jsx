import React from 'react'
import ReactDOM from 'react-dom'

import { AppIntl } from './components'
import SurveyorDispatcher from './surveyor'

// Include this to enable HMR for this module
if (module.hot) {
  module.hot.accept()
}

/*
This is the surveyors app
*/

const appElement = document.getElementById('surveyors-app')
const surveyorId = appElement.getAttribute('data-surveyor-id')
const action = appElement.getAttribute('data-action')

ReactDOM.render(
  <AppIntl>
    <SurveyorDispatcher action={action} surveyorId={surveyorId} />
  </AppIntl>,
  appElement
)
