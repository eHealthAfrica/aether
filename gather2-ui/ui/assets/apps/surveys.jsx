import React from 'react'
import ReactDOM from 'react-dom'

import { AppIntl, FetchUrlsContainer, PaginationContainer } from './components'
import { getSurveysAPIPath } from './utils/paths'

import Survey from './survey/Survey'
import SurveyForm from './survey/SurveyForm'
import SurveysList from './survey/SurveysList'

// Include this to enable HMR for this module
if (module.hot) {
  module.hot.accept()
}

/*
This is the surveys app
*/

const appElement = document.getElementById('surveys-app')
const surveyId = appElement.getAttribute('data-survey-id')
const action = appElement.getAttribute('data-action')

let component
switch (action) {
  case 'add':
    component = <SurveyForm survey={{}} />
    break

  case 'edit':
    const editUrls = [
      {
        name: 'survey',
        url: getSurveysAPIPath({id: surveyId})
      }
    ]

    component = <FetchUrlsContainer urls={editUrls} targetComponent={SurveyForm} />
    break

  case 'view':
    const viewUrls = [
      {
        name: 'survey',
        url: getSurveysAPIPath({id: surveyId, withStats: true})
      }
    ]

    component = <FetchUrlsContainer urls={viewUrls} targetComponent={Survey} />
    break

  default:
    component = (
      <PaginationContainer
        pageSize={12}
        url={getSurveysAPIPath({withStats: true})}
        position='top'
        listComponent={SurveysList}
        showPrevious
        showNext
      />
    )
    break
}

ReactDOM.render(<AppIntl>{ component }</AppIntl>, appElement)
