import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { PaginationContainer } from '../components'
import { getSurveysPath, getResponsesAPIPath } from '../utils/paths'

import SurveyDetail from './SurveyDetail'
import ResponsesList from '../response/ResponsesList'
import ResponsesItem from '../response/ResponsesItem'

const TABLE_SIZE = 10

export default class Survey extends Component {
  constructor (props) {
    super(props)

    this.state = {
      pageSize: TABLE_SIZE
    }
  }

  render () {
    const {survey} = this.props

    return (
      <div data-qa={`survey-item-${survey.id}`} className='survey-view'>
        <div className='survey-header'>
          <h2>{survey.name}</h2>
          <a
            href={getSurveysPath({action: 'edit', id: survey.id})}
            role='button'
            className='btn btn-primary btn-icon'>
            <i className='fa fa-pencil invert mr-3' />
            <FormattedMessage
              id='survey.view.action.edit'
              defaultMessage='Edit survey' />
          </a>
        </div>

        <SurveyDetail survey={survey} />

        { this.renderResponses() }
      </div>
    )
  }

  renderResponses () {
    const {survey} = this.props

    if (survey.responses === 0) {
      return ''
    }

    const {pageSize} = this.state
    const ResponseComponent = (pageSize === 1 ? ResponsesItem : ResponsesList)

    return (
      <div className='survey-data'>
        <div className='survey-data-toolbar'>
          <ul className='survey-data-tabs'>
            <li>
              <button
                className={`tab ${pageSize !== 1 ? 'active' : ''}`}
                onClick={() => { this.setState({ pageSize: TABLE_SIZE }) }}
                >
                <i className='fa fa-th-list mr-2' />
                <FormattedMessage
                  id='survey.view.action.table'
                  defaultMessage='Table' />
              </button>
            </li>
            <li>
              <button
                className={`tab ${pageSize === 1 ? 'active' : ''}`}
                onClick={() => { this.setState({ pageSize: 1 }) }}
                >
                <i className='fa fa-file mr-2' />
                <FormattedMessage
                  id='survey.view.action.single'
                  defaultMessage='Single' />
              </button>
            </li>
          </ul>
        </div>
        <PaginationContainer
          pageSize={pageSize}
          url={getResponsesAPIPath({surveyId: survey.id})}
          position='bottom'
          listComponent={ResponseComponent}
          showPrevious
          showNext
        />
      </div>
    )
  }
}
