import React from 'react'
import ReactDOM from 'react-dom'

import FetchUrlsContainer from './components/FetchUrlsContainer'

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
        url: `/core/surveys/${surveyId}.json`
      }
    ]

    component = (
      <FetchUrlsContainer urls={editUrls}>
        <SurveyForm />
      </FetchUrlsContainer>
    )
    break

  case 'view':
    const viewUrls = [
      {
        name: 'survey',
        url: `/core/surveys-stats/${surveyId}.json`
      },
      {
        name: 'responses',
        url: `/core/surveys/${surveyId}/responses.json`
      }
    ]

    component = (
      <FetchUrlsContainer urls={viewUrls}>
        <Survey />
      </FetchUrlsContainer>
    )
    break

  default:
    const listUrls = [
      {
        name: 'surveys',
        url: '/core/surveys-stats.json'
      }
    ]

    component = (
      <FetchUrlsContainer urls={listUrls}>
        <SurveysList />
      </FetchUrlsContainer>
    )
    break
}

ReactDOM.render(component, appElement)
