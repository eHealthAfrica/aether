import React, { Component } from 'react'
import { FormattedMessage, FormattedNumber } from 'react-intl'

import SurveyDates from './SurveyDates'

export default class SurveyDetail extends Component {
  render () {
    const {survey} = this.props

    return (
      <div data-qa={`survey-detail-${survey.id}`} className='survey-detail'>
        <div className='survey-dates'>
          <h5 className='title'>
            <FormattedMessage
              id='survey.detail.date'
              defaultMessage='Dates' />
          </h5>
          <SurveyDates survey={survey} showDuration />
        </div>

        <div className='survey-records'>
          <span className='record-number mr-1'>
            <FormattedNumber value={survey.submission_count} />
          </span>
          <FormattedMessage
            id='survey.detail.submissions'
            defaultMessage='records' />
        </div>
      </div>
    )
  }
}
