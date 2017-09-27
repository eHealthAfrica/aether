import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { flatten, inflate } from '../utils/types'
import { JSONViewer, FullDateTime } from '../components'

const SEPARATOR = '¬¬¬'  // very uncommon string

export default class ResponsesList extends Component {
  render () {
    const {list} = this.props

    if (list.length === 0) {
      return <div data-qa='responses-list-empty' />
    }

    // the first entry will decide the table columns
    const columns = Object.keys(flatten(list[0].data, SEPARATOR))

    return (
      <div data-qa='responses-list' className='x-0'>
        <div className='survey-content'>
          <table className='table table-sm'>
            { this.renderHeader(columns) }
            <tbody>
              { list.map((response, index) => this.renderResponse(response, index, columns)) }
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  renderHeader (columns) {
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

    const headers = inflate(columns, SEPARATOR)
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

  renderResponse (response, index, columns) {
    const flattenData = flatten({...response.data}, SEPARATOR)

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
