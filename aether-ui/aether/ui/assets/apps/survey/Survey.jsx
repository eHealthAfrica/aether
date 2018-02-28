import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { FetchUrlsContainer, PaginationContainer } from '../components'
import { range } from '../utils'
import { MAX_PAGE_SIZE, GATHER_APP } from '../utils/constants'
import { CSV_HEADER_RULES, CSV_HEADER_RULES_SEP } from '../utils/env'
import { getSurveysPath, getSurveysAPIPath, getSubmissionsAPIPath } from '../utils/paths'
import { postData } from '../utils/request'
import { flatten } from '../utils/types'

import SurveyDetail from './SurveyDetail'
import SurveyMasks from './SurveyMasks'
import SubmissionsList from '../submission/SubmissionsList'
import SubmissionItem from '../submission/SubmissionItem'

const TABLE_SIZE = 10
const SEPARATOR = '¬¬¬' // very uncommon string

export default class Survey extends Component {
  constructor (props) {
    super(props)

    this.state = {
      pageSize: TABLE_SIZE,
      total: props.submissions.count,
      allColumns: [],
      selectedColumns: []
    }

    const {results} = props.submissions
    if (results.length) {
      const allFlattenKeys = []

      // use the initial submissions to extract the possible columns
      results.forEach(result => {
        Object.keys(flatten(result.payload, SEPARATOR))
          .forEach(key => { allFlattenKeys.push(key) })
      })

      this.state.allColumns = [ ...new Set(allFlattenKeys) ]
      this.state.selectedColumns = [ ...this.state.allColumns ]
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

        { this.renderSubmissions() }
      </div>
    )
  }

  renderSubmissions () {
    const {survey} = this.props

    if (survey.submissions === 0) {
      return ''
    }

    const {pageSize} = this.state
    const SubmissionComponent = (pageSize === 1 ? SubmissionItem : SubmissionsList)
    const extras = {
      separator: SEPARATOR,
      columns: this.state.selectedColumns
    }

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
            <li>
              { this.renderDownloadButton() }
            </li>
            <li className='toolbar-filter'>
              { this.renderMaskButton() }
            </li>
          </ul>
        </div>
        <PaginationContainer
          pageSize={pageSize}
          url={getSubmissionsAPIPath({mapping: survey.id})}
          position='top'
          listComponent={SubmissionComponent}
          search
          showPrevious
          showNext
          extras={extras}
        />
      </div>
    )
  }

  renderDownloadButton () {
    const {survey} = this.props
    const {total, allColumns, selectedColumns} = this.state

    const pageSize = MAX_PAGE_SIZE
    const sep = CSV_HEADER_RULES_SEP
    const params = {
      mapping: survey.id,
      fields: 'created,payload',
      // using different format than `json` will build the "post as get" API path
      format: 'csv',
      pageSize
    }
    const payload = {
      // remove "payload.None." prefix from headers labels
      // from "payload.None.a.b.c" to "a.b.c"
      parse_columns: `remove-prefix${sep}payload.,remove-prefix${sep}None.,${CSV_HEADER_RULES}`,
      rule_sep: sep
    }

    // restrict the columns to export with the selected columns
    if (selectedColumns.length !== allColumns.length) {
      payload.columns = 'created,' + selectedColumns
        .map(key => 'payload.' + key.replace(new RegExp(SEPARATOR, 'g'), '.'))
        .join(',')
    }

    const download = (options, fileName) => {
      postData(getSubmissionsAPIPath(options), payload, {download: true, fileName})
        .catch(err => { console.log(err) })
    }

    if (total < pageSize) {
      return (
        <button
          className='tab'
          onClick={() => { download(params, `${survey.name}.csv`) }}
        >
          <i className='fa fa-download mr-2' />
          <FormattedMessage
            id='survey.view.action.download'
            defaultMessage='Download' />
        </button>
      )
    }

    const dropdown = 'downloadLinkChoices'
    const pages = range(1, Math.ceil(total / pageSize) + 1)
      .map(index => ({
        key: index,
        options: { ...params, page: index },
        fileName: `${survey.name}-${index}.csv`
      }))

    return (
      <div className='dropdown'>
        <button
          className='tab'
          id={dropdown}
          data-toggle='dropdown'
        >
          <i className='fa fa-download mr-2' />
          <FormattedMessage
            id='survey.view.action.download'
            defaultMessage='Download' />
        </button>

        <div
          className='dropdown-menu'
          aria-labelledby={dropdown}
        >
          <div className='dropdown-list'>
            {
              pages.map(page => (
                <button
                  key={page.key}
                  className='dropdown-item'
                  onClick={() => { download(page.options, page.fileName) }}
                >
                  { page.fileName }
                </button>
              ))
            }
          </div>
        </div>
      </div>
    )
  }

  renderMaskButton () {
    if (this.state.allColumns.length === 0) {
      return ''
    }

    const handleResponse = (response) => ({
      ...response,
      columns: this.state.allColumns,
      separator: SEPARATOR,
      onChange: (selectedColumns) => { this.setState({ selectedColumns }) }
    })

    const urls = [
      {
        name: 'survey',
        url: getSurveysAPIPath({ app: GATHER_APP, id: this.props.survey.id }),
        force: {
          url: getSurveysAPIPath({ app: GATHER_APP }),
          data: { mapping_id: this.props.survey.id, name: this.props.survey.name }
        }
      }
    ]

    return <FetchUrlsContainer
      urls={urls}
      handleResponse={handleResponse}
      targetComponent={SurveyMasks}
    />
  }
}
