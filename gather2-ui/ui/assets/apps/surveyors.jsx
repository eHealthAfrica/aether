import React from 'react'
import ReactDOM from 'react-dom'

import FetchUrlsContainer from './components/FetchUrlsContainer'
import SurveyorsList from './surveyor/SurveyorsList'

// Include this to enable HMR for this module
if (module.hot) {
  module.hot.accept()
}

/*
This is the surveyors app
*/

ReactDOM.render(
  <FetchUrlsContainer urls={[
    {
      name: 'surveyors',
      url: '/odk/surveyors.json'
    }
  ]}>
    <SurveyorsList />
  </FetchUrlsContainer>,
  document.getElementById('surveyors-app')
)
