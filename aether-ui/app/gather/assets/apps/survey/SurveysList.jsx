import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import SurveyCard from './SurveyCard'

export default class SurveysList extends Component {
  render () {
    const {list} = this.props

    if (list.length === 0) {
      return <div data-qa='surveys-list-empty' />
    }

    return (
      <div data-qa='surveys-list' className='surveys-list'>
        <h4 className='title'>
          <FormattedMessage
            id='survey.list.title'
            defaultMessage='Surveys' />
        </h4>

        <div className='surveys-list-cards'>
          {
            list.map(survey => (
              <SurveyCard
                key={survey.id}
                className='col-6 col-sm-4 col-md-3'
                survey={survey}
              />
            ))
          }
        </div>
      </div>
    )
  }
}
