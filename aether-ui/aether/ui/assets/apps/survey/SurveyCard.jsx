import React, { Component } from 'react'
import { FormattedMessage, FormattedNumber } from 'react-intl'

import { getSurveysPath } from '../utils/paths'
import SurveyDates from './SurveyDates'

export default class SurveyCard extends Component {
  render () {
    const {survey} = this.props

    return (
      <a
        data-qa={`survey-card-${survey.id}`}
        href={getSurveysPath({action: 'view', id: survey.id})}
        className='card'>
        <h3 className='card-header'>{survey.name}</h3>
        <div className='card-block'>
          <SurveyDates survey={survey} />

          <p className='card-display text-center'>
            <span className='card-number'>
              <FormattedNumber value={survey.submission_count || 0} />
            </span>
            <FormattedMessage
              id='survey.card.submissions'
              defaultMessage='records' />
          </p>
        </div>
      </a>
    )
  }
}
