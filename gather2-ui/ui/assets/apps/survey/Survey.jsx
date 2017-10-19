import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { PaginationContainer } from '../components'
import { getSurveysPath, getResponsesAPIPath } from '../utils/paths'
import { flatten, cleanPropertyName } from '../utils/types'

import SurveyDetail from './SurveyDetail'
import ResponsesList from '../response/ResponsesList'
import ResponsesItem from '../response/ResponsesItem'

const TABLE_SIZE = 10
const SEPARATOR = '¬¬¬'  // very uncommon string

export default class Survey extends Component {
  constructor (props) {
    super(props)

    this.state = {
      pageSize: TABLE_SIZE
    }

    if (props.response.results.length) {
      this.state.columns = []
      Object.keys(flatten(props.response.results[0].data, SEPARATOR))
            .forEach(key => { this.state.columns[key] = true })
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
    const extras = (pageSize === 1
      ? {}
      : {
        separator: SEPARATOR,
        columns: Object.keys(this.state.columns || {})
                       .filter(key => this.state.columns[key])
      }
    )

    return (
      <div className='survey-data'>
        <div className='survey-data-toolbar'>
          <ul className='survey-data-tabs'>
            <li>
              <button
                className={`tab ${pageSize !== 1 ? 'active' : ''}`}
                onClick={() => { this.setState({ pageSize: TABLE_SIZE, showColumns: false }) }}
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
                onClick={() => { this.setState({ pageSize: 1, showColumns: false }) }}
                >
                <i className='fa fa-file mr-2' />
                <FormattedMessage
                  id='survey.view.action.single'
                  defaultMessage='Single' />
              </button>
            </li>
            <li className='toolbar-filter'>
              { this.renderColumnsBar() }
              { this.renderColumnsFilter() }
            </li>
          </ul>
        </div>
        <PaginationContainer
          pageSize={pageSize}
          url={getResponsesAPIPath({surveyId: survey.id})}
          position='top'
          listComponent={ResponseComponent}
          search
          showPrevious
          showNext
          extras={extras}
        />
      </div>
    )
  }

  renderColumnsBar () {
    if (!this.state.columns || this.state.pageSize === 1) {
      return ''
    }

    const selectAll = () => {
      const columns = {...this.state.columns}
      Object.keys(columns).forEach(key => { columns[key] = true })
      this.setState({ columns, showColumns: false })
    }

    const columns = Object.keys(this.state.columns)
                          .filter(key => this.state.columns[key])
    const allChecked = Object.keys(this.state.columns).length === columns.length

    return (
      <div className='pull-right filter-toggles'>
        <FormattedMessage
          id='response.list.table.action.columns'
          defaultMessage='Columns:' />
        <button
          className={`btn badge ${allChecked ? 'active' : ''}`}
          onClick={selectAll}
          >
          <FormattedMessage
            id='response.list.table.action.columns.all'
            defaultMessage='Show all' />
        </button>
        <FormattedMessage
          id='response.list.table.action.columns.or'
          defaultMessage='or' />
        <button
          className={`btn badge ${!allChecked ? 'active' : ''}`}
          onClick={() => { this.setState({ showColumns: !this.state.showColumns }) }}
          >
          {
            this.state.showColumns
            ? <FormattedMessage
              id='response.list.table.action.columns.select.hide'
              defaultMessage='hide selected' />
            : <FormattedMessage
              id='response.list.table.action.columns.select.show'
              defaultMessage='show selected' />
          }
        </button>
      </div>
    )
  }

  renderColumnsFilter () {
    const toggleColumn = (key) => {
      const columns = {...this.state.columns}
      columns[key] = !columns[key]
      this.setState({ columns })
    }
    const getClassName = (key) => this.state.columns[key] ? 'fa-check-circle' : 'fa-circle-o'

    return (
      <div
        className={`filter-container ${this.state.showColumns ? 'active' : ''}`}>
        {
          this.state.showColumns &&
          <div className='columns-filter'>
            <ul>
              {
                Object.keys(this.state.columns).map(key => (
                  <li
                    key={key}
                    className='column-title'
                    onClick={() => toggleColumn(key)}>
                    <i className={`fa ${getClassName(key)} mr-2`} />
                    <span>
                      { cleanPropertyName(key.split(SEPARATOR).join(' - ')) }
                    </span>
                  </li>
                ))
              }
            </ul>
            <button
              className='btn btn-primary pull-right'
              onClick={() => { this.setState({ showColumns: false }) }}
              >
              <FormattedMessage
                id='response.list.table.action.columns.ok'
                defaultMessage='OK' />
            </button>
          </div>
        }
      </div>
    )
  }
}
