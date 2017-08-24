import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import SurveyCard from './SurveyCard'

export default class SurveysList extends Component {
  render () {
    const {list} = this.props

    return (
      <div data-qa='surveys-list' className='surveys-list'>
        <div className='surveys-list__header'>
          <h1>eHealth Africa (Org name)</h1>
          <div>
            <a href='/surveys/add/' role='button' className='btn btn-primary btn-icon'>
              <i className='fa fa-plus-circle' />
              &nbsp;
              <FormattedMessage
                id='survey.list.action.add'
                defaultMessage='New survey' />
            </a>
          </div>
        </div>

        {
          list.length > 0 &&
          <div>
            <h4 className='title'>
              <FormattedMessage
                id='survey.list.title'
                defaultMessage='Surveys' />
            </h4>
            <div className='surveys-list__cards justify-content-md-start'>
              {
                list.map(survey => <SurveyCard className='col-6 col-sm-4 col-md-3' key={survey.id} survey={survey} />)
              }
            </div>
          </div>
        }
      </div>
    )
  }
}
