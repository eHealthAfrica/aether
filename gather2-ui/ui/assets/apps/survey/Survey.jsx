import React, { Component } from 'react'

import SurveyCard from './SurveyCard'

export default class Survey extends Component {
  render () {
    const {survey} = this.props

    return (
      <div className='survey-view' data-qa={`survey-item-${survey.id}`}>
        <div className='survey__header'>
          <h2>{survey.name}</h2>
          <a href={`/surveys/edit/${survey.id}`} role='button' className='btn btn-primary btn-icon'>
            <i className='fa fa-pencil' />
            Edit survey
          </a>
        </div>

        <div className='row'>
          <SurveyCard survey={survey} />
        </div>
      </div>
    )
  }
}
