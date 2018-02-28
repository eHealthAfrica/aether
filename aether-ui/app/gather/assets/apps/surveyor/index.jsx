import React, { Component } from 'react'

import { FetchUrlsContainer, PaginationContainer } from '../components'
import { getSurveyorsAPIPath } from '../utils/paths'
import { ODK_ACTIVE } from '../utils/env'

import SurveyorForm from './SurveyorForm'
import SurveyorsList from './SurveyorsList'

export default class SurveyorDispatcher extends Component {
  render () {
    const {action, surveyorId} = this.props

    // ODK check
    if (!ODK_ACTIVE) {
      // blank page
      return <div />
    }

    switch (action) {
      case 'add':
        return <SurveyorForm surveyor={{}} />

      case 'edit':
        const editUrls = [
          {
            name: 'surveyor',
            url: getSurveyorsAPIPath({id: surveyorId})
          }
        ]

        return <FetchUrlsContainer urls={editUrls} targetComponent={SurveyorForm} />

      default:
        return (
          <PaginationContainer
            pageSize={36}
            url={getSurveyorsAPIPath({})}
            position='top'
            listComponent={SurveyorsList}
            search
            showPrevious
            showNext
          />
        )
    }
  }
}
