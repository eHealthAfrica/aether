import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { ORG_NAME } from '../utils/env'

export default class SurveyorsList extends Component {
  render () {
    const {list} = this.props

    return (
      <div data-qa='surveyors-list' className='page-container'>
        <div className='page-header'>
          <h1 data-qa='organization-name'>{ ORG_NAME }</h1>
          <div>
            <a href='/surveyors/add/' role='button' className='btn btn-primary btn-icon'>
              <i className='fa fa-plus-circle mr-3' />
              <FormattedMessage
                id='surveyor.list.action.add'
                defaultMessage='New surveyor' />
            </a>
          </div>
        </div>

        {
          list.length > 0 &&
          <div className='page-content'>
            <h4 className='title'>
              <FormattedMessage
                id='surveyor.list.title'
                defaultMessage='Surveyors' />
            </h4>

            <div className='surveyors'>
              {
                list.map((surveyor) => (
                  <div key={surveyor.id} className='surveyor-list-item'>
                    <div className='surveyor-header'>
                      <i className='fa fa-user mr-2' />
                      {surveyor.username}

                      <a
                        href={`/surveyors/edit/${surveyor.id}`}
                        role='button'
                        className='btn btn-sm btn-secondary icon-only pull-right'>
                        <i className='fa fa-pencil' />
                      </a>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        }
      </div>
    )
  }
}
