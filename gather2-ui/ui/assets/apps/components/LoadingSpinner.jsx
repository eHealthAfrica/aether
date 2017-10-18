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
      <div data-qa='data-loading' className='container-fluid'>
        <p className='alert alert-info'>
          <i className='loading-spinner mr-2' />
          <FormattedMessage
            id='alert.loading'
            defaultMessage='Loading data from server…' />
        </p>
      </div>
    )
  }
}
