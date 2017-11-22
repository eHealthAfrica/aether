import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { flatten, inflate } from '../utils/types'
import { JSONViewer, FullDateTime } from '../components'

export default class ResponsesList extends Component {
  render () {
    const {list} = this.props

    if (list.length === 0) {
      return <div data-qa='responses-list-empty' />
    }

    return (
      <div data-qa='responses-list' className='x-0'>
        <div className='survey-content'>
          <table className='table table-sm'>
            { this.renderHeader() }
            <tbody>
              { list.map((response, index) => this.renderResponse(response, index)) }
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

    if (rows === 0) {
      // empty first row???
      return (
        <thead>
          <tr>
            <th />
            <th>
              <FormattedMessage
                id='response.list.table.created'
                defaultMessage='Submitted' />
            </th>
          </tr>
        </thead>
      )
    }

    return (
      <thead>
        {
          headers.map((row, index) => (
            <tr key={index}>
              {
                (index === 0) &&
                <th rowSpan={rows} />
              }
              {
                (index === 0) &&
                <th rowSpan={rows}>
                  <FormattedMessage
                    id='response.list.table.created'
                    defaultMessage='Submitted' />
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

  renderResponse (response, index) {
    const {columns, separator} = this.props
    const flattenData = flatten({...response.data}, separator)

    return (
      <tr data-qa={`response-row-${response.id}`} key={response.id}>
        <td scope='row'>{this.props.start + index}</td>
        <td>
          <FullDateTime date={response.created} />
        </td>

        {
          columns.map(key => (
            <td key={key}>
              <JSONViewer data={flattenData[key]} />
            </td>
          ))
        }
      </tr>
    )
  }
}
