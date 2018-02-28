import React from 'react'
import ReactDOM from 'react-dom'

import { AppIntl } from './components'
import SurveyDispatcher from './survey'

// Include this to enable HMR for this module
if (module.hot) {
  module.hot.accept()
}

/*
This is the surveys/surveys app.

An Aether "Mapping" is equivalent to a Gather "Survey".
*/

const appElement = document.getElementById('surveys-app')
const surveyId = appElement.getAttribute('data-survey-id')
const action = appElement.getAttribute('data-action')

ReactDOM.render(
  <AppIntl>
    <SurveyDispatcher action={action} surveyId={surveyId} />
  </AppIntl>,
  appElement
)
