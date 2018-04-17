import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

/**
 * LoadingSpinner component.
 *
 * Renders a spinner indicating that data is being loaded from server.
 */

export default class LoadingSpinner extends Component {
  render () {
    return (
      <div data-qa='data-loading' className='loading-container'>
        <div className='loading-info'>
          <div className='loading-spinner'>
            <div className='dot1' />
            <div className='dot2' />
            <div className='dot3' />
            <div className='dot4' />
            <div className='dot5' />
            <div className='dot6' />
          </div>
          <FormattedMessage
            id='alert.loading'
            defaultMessage='Loading data from server…' />
        </div>
      </div>
    )
  }
}
