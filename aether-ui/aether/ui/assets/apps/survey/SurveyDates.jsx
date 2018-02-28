import React, { Component } from 'react'
import { FormattedDate, FormattedMessage, FormattedNumber } from 'react-intl'
import moment from 'moment'

export default class SurveyDates extends Component {
  render () {
    const {survey} = this.props

    return (
      <div
        data-qa={`survey-dates-${survey.id}`}
        className='card-block'>
        <p className='card-text small'>
          <span className='card-dates pr-2'>
            <span className='label mr-1'>
              <FormattedMessage
                id='survey.dates.created'
                defaultMessage='Created at' />
            </span>
            <FormattedDate
              value={survey.created}
              year='numeric'
              month='short'
              day='numeric' />
          </span>

          { survey.submission_count === 0 && this.renderNoSubmissions() }
          { survey.submission_count > 0 && this.renderSubmissions() }
          {
            survey.submission_count > 0 &&
            this.props.showDuration &&
            this.renderSubmissionsDuration()
          }
        </p>
      </div>
    )
  }

  renderNoSubmissions () {
    return (
      <span className='label mr-1'>
        <FormattedMessage
          id='survey.dates.submissions.zero'
          defaultMessage='no data entry' />
      </span>
    )
  }

  renderSubmissions () {
    const {survey} = this.props
    const days = moment(survey.last_submission).diff(moment(survey.first_submission), 'days')

    if (days === 0) {
      return (
        <span className='card-dates pr-2'>
          <span className='label mr-1'>
            <FormattedMessage
              id='survey.dates.submissions.on'
              defaultMessage='data entry on' />
          </span>
          <FormattedDate
            value={survey.first_submission}
            year='numeric'
            month='short'
            day='numeric' />
        </span>
      )
    }

    return (
      <span className='card-dates pr-2'>
        <span className='label mr-1'>
          <FormattedMessage
            id='survey.dates.submissions.from'
            defaultMessage='data entry from' />
        </span>
        <FormattedDate
          value={survey.first_submission}
          year='numeric'
          month='short'
          day='numeric' />
        <span className='label mr-1'>
          <FormattedMessage
            id='survey.dates.submissions.to'
            defaultMessage='to' />
        </span>
        <FormattedDate
          value={survey.last_submission}
          year='numeric'
          month='short'
          day='numeric' />
      </span>
    )
  }

  renderSubmissionsDuration () {
    const {survey} = this.props
    const days = moment(survey.last_submission).diff(moment(survey.first_submission), 'days') + 1

    return (
      <span className='card-dates'>
        <span className='label mr-1'>
          <FormattedMessage
            id='survey.dates.submissions.duration'
            defaultMessage='duration' />
        </span>
        <FormattedNumber value={days} />
        <span className='ml-1'>
          <FormattedMessage
            id='survey.dates.submissions.duration.days'
            defaultMessage='days' />
        </span>
      </span>
    )
  }
}
