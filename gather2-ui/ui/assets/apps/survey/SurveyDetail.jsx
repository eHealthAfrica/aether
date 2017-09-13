import React, { Component } from 'react'
import { FormattedMessage, FormattedNumber } from 'react-intl'

import SurveyDates from './SurveyDates'

export default class SurveyDetail extends Component {
  render () {
    const {survey} = this.props

    return (
      <div className='survey-detail' data-qa={`survey-detail-${survey.id}`}>
        <div className='survey-dates'>
          <h5 className='title'>
            <FormattedMessage
              id='survey.detail.date'
              defaultMessage='Dates' />
          </h5>
          <SurveyDates survey={survey} showDuration />
        </div>

        <div className='survey-schema'>
          <h5 className='title'>
            <FormattedMessage
              id='survey.detail.schema'
              defaultMessage='Schema' />
          </h5>
          <pre>{JSON.stringify(survey.schema, 0, 2)}</pre>
        </div>

        <div className='survey-records'>
          <span className='record-number mr-1'>
            <FormattedNumber value={survey.responses} />
          </span>
          <FormattedMessage
            id='survey.detail.responses'
            defaultMessage='records' />
        </div>
      </div>
    )
  }
}
