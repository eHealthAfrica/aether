import React, { Component } from 'react'
import { FormattedDate, FormattedMessage, FormattedNumber } from 'react-intl'

export default class SurveyCard extends Component {
  render () {
    const {survey} = this.props

    return (
      <a
        data-qa={`survey-card-${survey.id}`}
        href={`/surveys/view/${survey.id}`}
        className='card'>
        <h3 className='card-header'>{survey.name}</h3>
        <div className='card-block'>
          <p className='card-text small'>
            <span className='card-dates pr-2'>
              <span className='label mr-1'>
                <FormattedMessage
                  id='survey.card.created'
                  defaultMessage='created' />
              </span>
              <FormattedDate
                value={survey.created}
                year='numeric'
                month='short'
                day='numeric' />
            </span>

            { survey.responses > 0 &&
              <span className='card-dates ml-2'>
                <span className='label mr-1'>
                  <FormattedMessage
                    id='survey.card.responses.from'
                    defaultMessage='data entry from' />
                </span>
                <FormattedDate
                  value={survey.first_response}
                  year='numeric'
                  month='short'
                  day='numeric' />
                <span className='label mx-1'>
                  <FormattedMessage
                    id='survey.card.responses.to'
                    defaultMessage='to' />
                </span>
                <FormattedDate
                  value={survey.last_response}
                  year='numeric'
                  month='short'
                  day='numeric' />
              </span>
            }

            { survey.responses === 0 &&
              <FormattedMessage
                id='survey.card.responses.zero'
                defaultMessage='no data entry' />
            }

          </p>
          <p className='card-display text-center'>
            <span className='card-number'>
              <FormattedNumber value={survey.responses} />
            </span>
            <FormattedMessage
              id='survey.card.responses'
              defaultMessage='records' />
          </p>
        </div>
      </a>
    )
  }
}
