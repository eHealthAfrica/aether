import React from 'react'
import ReactDOM from 'react-dom'
import { IntlProvider } from 'react-intl'

import { PaginationContainer } from './components'
import SurveyorsList from './surveyor/SurveyorsList'

// Include this to enable HMR for this module
if (module.hot) {
  module.hot.accept()
}

/*
This is the surveyors app
*/

ReactDOM.render(
  <IntlProvider defaultLocale='en' locale={navigator.locale || 'en'}>
    <PaginationContainer
      pageSize={36}
      url='/odk/surveyors.json?page='
      listComponent={SurveyorsList}
    />
  </IntlProvider>,
  document.getElementById('surveyors-app')
)
