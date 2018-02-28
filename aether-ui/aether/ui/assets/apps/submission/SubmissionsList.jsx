import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { flatten, inflate } from '../utils/types'
import { JSONViewer, FullDateTime } from '../components'

export default class SubmissionsList extends Component {
  render () {
    const {list} = this.props

    if (list.length === 0) {
      return <div data-qa='submissions-list-empty' />
    }

    return (
      <div data-qa='submissions-list' className='x-0'>
        <div className='survey-content'>
          <table className='table table-sm'>
            { this.renderHeader() }
            <tbody>
              { list.map((submission, index) => this.renderSubmission(submission, index)) }
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  renderHeader () {
    /****************************************************************
        Data
        ====
        {
          a: {
            b: {
              c: 1,
              d: 2
            },
            e: {
              f: true
            },
            g: []
          },
          h: 0
        }

        Table header
        ============
        +---+------------++----------------+---+
        | # | Submitted  | A              | H |
        |   |            +-------+---+----+   |
        |   |            | B     | E | G  |   |
        |   |            +---+---+---+    |   |
        |   |            | C | D | F |    |   |
        +---+------------+---+---+---+----+---+
        | 1 | 1999-01-01 | 1 | 2 | T | [] | 0 |
        +---+------------+---+---+---+----+---+

    ****************************************************************/

    const {columns, separator} = this.props
    const headers = inflate(columns, separator)
    const rows = headers.length

    return (
      <thead>
        {
          headers.map((row, index) => (
            <tr key={index}>
              {
                (index === 0) &&
                <th rowSpan={rows || 1} />
              }
              {
                (index === 0) &&
                <th rowSpan={rows || 1}>
                  <FormattedMessage
                    id='submission.list.table.date'
                    defaultMessage='Submitted' />
                </th>
              }
              {
                (index === 0) &&
                <th rowSpan={rows || 1}>
                  <FormattedMessage
                    id='submission.list.table.revision'
                    defaultMessage='Revision' />
                </th>
              }
              {
                (index === 0) &&
                <th rowSpan={rows || 1}>
                  <FormattedMessage
                    id='submission.list.table.survey.revision'
                    defaultMessage='Survey revision' />
                </th>
              }

              {
                Object.keys(row).map(column => (
                  <th
                    key={row[column].key}
                    title={row[column].path}
                    rowSpan={row[column].isLeaf ? (rows - index) : 1}
                    colSpan={row[column].siblings}>
                    { row[column].label }
                  </th>
                ))
              }
            </tr>
          ))
        }
      </thead>
    )
  }

  renderSubmission (submission, index) {
    const {columns, separator} = this.props
    const flattenPayload = flatten({...submission.payload}, separator)

    return (
      <tr data-qa={`submission-row-${submission.id}`} key={submission.id}>
        <td scope='row'>{this.props.start + index}</td>
        <td>
          <FullDateTime date={submission.date} />
        </td>
        <td>
          {submission.revision}
        </td>
        <td>
          {submission.map_revision}
        </td>

        {
          columns.map(key => (
            <td key={key}>
              <JSONViewer data={flattenPayload[key]} />
            </td>
          ))
        }
      </tr>
    )
  }
}
