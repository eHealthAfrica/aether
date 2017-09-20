import React, { Component } from 'react'
import {
  FormattedDate,
  FormattedMessage,
  FormattedRelative,
  FormattedTime
} from 'react-intl'

import { JSONViewer } from '../components'

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
          <div className='property'>
            <h5 className='property-title'>
              <FormattedMessage
                id='response.view.created'
                defaultMessage='Submitted' />
            </h5>
            <div className='property-value'>
              <span className='mr-2'>
                <FormattedDate
                  value={response.created}
                  year='numeric'
                  month='long'
                  day='numeric' />
              </span>
              <span className='mr-2'>
                <FormattedTime
                  value={response.created}
                  hour12={false}
                  hour='2-digit'
                  minute='2-digit'
                  second='2-digit'
                  timeZoneName='short' />
              </span>
              <span>
                (<FormattedRelative value={response.created} />)
              </span>
            </div>
          </div>

          <div>
            <JSONViewer data={response.data} />
          </div>
        </div>
      </div>
    )
  }
}
