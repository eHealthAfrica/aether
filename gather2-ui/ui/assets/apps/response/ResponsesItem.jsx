import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { JSONViewer, FullDateTime } from '../components'

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
              <FullDateTime date={response.created} />
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
