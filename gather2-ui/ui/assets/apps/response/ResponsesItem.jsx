import React, { Component } from 'react'
import { FormattedDate, FormattedMessage } from 'react-intl'

export default class ResponsesItem extends Component {
  render () {
    const {list} = this.props

    if (list.length !== 1) {
      return <div />
    }

    // assumption: there is only one item
    const response = list[0]

    return (
      <div data-qa={`response-item-${response.id}`} className='x-2'>
        <div className='survey-content single'>
          <div>
            <h5 className='title'>
              <FormattedMessage
                id='response.view.created'
                defaultMessage='Submitted' />
            </h5>
            <FormattedDate
              value={response.created}
              year='numeric'
              month='short'
              day='numeric' />
          </div>

          <div>
            <h5 className='title'>
              <FormattedMessage
                id='response.view.data'
                defaultMessage='Data' />
            </h5>

            <pre>{JSON.stringify(response.data, 0, 2)}</pre>
          </div>
        </div>
      </div>
    )
  }
}
