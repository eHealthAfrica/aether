import React from 'react'
import ReactDOM from 'react-dom'

import PaginationContainer from './components/PaginationContainer'
import SurveyorsList from './surveyor/SurveyorsList'

// Include this to enable HMR for this module
if (module.hot) {
  module.hot.accept()
}

/*
This is the surveyors app
*/

ReactDOM.render(
  <PaginationContainer
    pageSize={36}
    url='/odk/surveyors.json?page='
    listComponent={SurveyorsList}
  />,
  document.getElementById('surveyors-app')
)
