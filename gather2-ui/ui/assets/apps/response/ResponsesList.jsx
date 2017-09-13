import React, { Component } from 'react'
import { FormattedDate, FormattedMessage } from 'react-intl'

export default class ResponsesList extends Component {
  render () {
    const {list} = this.props

    return (
      <div data-qa='responses-list' className='x-0'>
        {
          list.length > 0 &&
          <div className='survey-content'>
            <table className='table table-bordered table-hover table-sm'>
              <thead>
                <tr>
                  <th>#</th>
                  <th>
                    <FormattedMessage
                      id='response.list.table.created'
                      defaultMessage='Submitted' />
                  </th>
                  <th>
                    <FormattedMessage
                      id='response.list.table.data'
                      defaultMessage='Data' />
                  </th>
                </tr>
              </thead>
              <tbody>
                { list.map((response, index) => this.renderResponse(response, index)) }
              </tbody>
            </table>
          </div>
        }
      </div>
    )
  }

  renderResponse (response, index) {
    return (
      <tr data-qa={`response-row-${response.id}`} key={response.id}>
        <td scope='row'>{this.props.start + index}</td>
        <td>
          <FormattedDate
            value={response.created}
            year='numeric'
            month='short'
            day='numeric' />
        </td>
        <td>
          <pre>{JSON.stringify(response.data, 0, 2)}</pre>
        </td>
      </tr>
    )
  }
}
