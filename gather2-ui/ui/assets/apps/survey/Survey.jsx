import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import SurveyCard from './SurveyCard'

export default class Survey extends Component {
  render () {
    const {survey} = this.props

    return (
      <div data-qa={`survey-item-${survey.id}`} className='survey-view'>
        <div className='survey-header'>
          <h2>{survey.name}</h2>
          <a href={`/surveys/edit/${survey.id}`} role='button' className='btn btn-primary btn-icon'>
            <i className='fa fa-pencil invert mr-3' />
            <FormattedMessage
              id='survey.view.action.edit'
              defaultMessage='Edit survey' />
          </a>
        </div>

        <div className='row'>
          <SurveyCard survey={survey} />
        </div>
      </div>
    )
  }
}
