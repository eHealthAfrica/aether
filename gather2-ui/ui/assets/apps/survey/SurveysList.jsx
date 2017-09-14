import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { ORG_NAME } from '../utils/env'
import SurveyCard from './SurveyCard'

export default class SurveysList extends Component {
  render () {
    const {list} = this.props

    return (
      <div data-qa='surveys-list' className='page-container'>
        <div className='page-header'>
          <h1 data-qa='organization-name'>{ ORG_NAME }</h1>
          <div>
            <a href='/surveys/add/' role='button' className='btn btn-primary btn-icon'>
              <i className='fa fa-plus-circle mr-3' />
              <FormattedMessage
                id='survey.list.action.add'
                defaultMessage='New survey' />
            </a>
          </div>
        </div>

        {
          list.length > 0 &&
          <div className='page-content'>
            <h4 className='title'>
              <FormattedMessage
                id='survey.list.title'
                defaultMessage='Surveys' />
            </h4>

            <div className='surveys-list-cards'>
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
