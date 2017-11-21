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
                defaultMessage='created' />
            </span>
            <FormattedDate
              value={survey.created}
              year='numeric'
              month='short'
              day='numeric' />
          </span>

          { survey.responses === 0 && this.renderNoResponses() }
          { survey.responses > 0 && this.renderResponses() }
          {
            survey.responses > 0 &&
            this.props.showDuration &&
            this.renderResponsesDuration()
          }
        </p>
      </div>
    )
  }

  renderNoResponses () {
    return (
      <span className='label mr-1'>
        <FormattedMessage
          id='survey.dates.responses.zero'
          defaultMessage='no data entry' />
      </span>
    )
  }

  renderResponses () {
    const {survey} = this.props
    const days = moment(survey.last_response).diff(moment(survey.first_response), 'days')

    if (days === 0) {
      return (
        <span className='card-dates pr-2'>
          <span className='label mr-1'>
            <FormattedMessage
              id='survey.dates.responses.on'
              defaultMessage='data entry on' />
          </span>
          <FormattedDate
            value={survey.first_response}
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
            id='survey.dates.responses.from'
            defaultMessage='data entry from' />
        </span>
        <FormattedDate
          value={survey.first_response}
          year='numeric'
          month='short'
          day='numeric' />
        <span className='label mr-1'>
          <FormattedMessage
            id='survey.dates.responses.to'
            defaultMessage='to' />
        </span>
        <FormattedDate
          value={survey.last_response}
          year='numeric'
          month='short'
          day='numeric' />
      </span>
    )
  }

  renderResponsesDuration () {
    const {survey} = this.props
    const days = moment(survey.last_response).diff(moment(survey.first_response), 'days') + 1

    return (
      <span className='card-dates'>
        <span className='label mr-1'>
          <FormattedMessage
            id='survey.dates.responses.duration'
            defaultMessage='duration' />
        </span>
        <FormattedNumber value={days} />
        <span className='ml-1'>
          <FormattedMessage
            id='survey.dates.responses.duration.days'
            defaultMessage='days' />
        </span>
      </span>
    )
  }
}
