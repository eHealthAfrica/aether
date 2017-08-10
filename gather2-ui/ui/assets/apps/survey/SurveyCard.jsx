import React, { Component } from 'react'
import moment from 'moment'

const DATE_FORMAT = 'DD.MM.YYYY'

export default class SurveyCard extends Component {
  render () {
    const {survey} = this.props

    return (
      <a href={`/surveys/view/${survey.id}`} className='card'>
        <h3 className='card-header'>{survey.name}</h3>
        <div className='card-block'>
          <p className='card-text small'>
            <span className='card-dates'><span className='label'>created</span> { moment(survey.created).format(DATE_FORMAT) } </span>

            { survey.responses > 0 &&
              <span className='card-dates'>
                <span className='label'>data entry from</span>
                <span> { moment(survey.first_response).format(DATE_FORMAT) } </span>
                <span className='label'>to</span>
                <span> { moment(survey.last_response).format(DATE_FORMAT) } </span>
              </span>
            }

            { survey.responses === 0 &&
              <span>no data entry</span>
            }

          </p>
          <p className='card-display text-center'>
            <span className='card-number'>{survey.responses}</span>
            records
          </p>
        </div>
      </a>
    )
  }
}
