import React from 'react'
import ReactDOM from 'react-dom'

import { AppIntl, FetchUrlsContainer, PaginationContainer } from './components'

import SurveyorForm from './surveyor/SurveyorForm'
import SurveyorsList from './surveyor/SurveyorsList'

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

let component
switch (action) {
  case 'add':
    component = <SurveyorForm surveyor={{}} />
    break

  case 'edit':
    const editUrls = [
      {
        name: 'surveyor',
        url: `/odk/surveyors/${surveyorId}.json`
      }
    ]

    component = <FetchUrlsContainer urls={editUrls} targetComponent={SurveyorForm} />
    break

  default:
    component = (
      <PaginationContainer
        pageSize={36}
        url='/odk/surveyors.json?'
        listComponent={SurveyorsList}
      />
    )
    break
}

ReactDOM.render(<AppIntl>{ component }</AppIntl>, appElement)
