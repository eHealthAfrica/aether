import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

/**
 * EmptyAlert component.
 *
 * Renders an alert message indicating that no data was found
 * while requesting it from server.
 */

export default class EmptyAlert extends Component {
  render () {
    return (
      <div data-qa='data-empty' className='container-fluid'>
        <p className='alert alert-danger'>
          <i className='fas fa-exclamation-triangle mr-1' />
          <FormattedMessage
            id='alert.empty'
            defaultMessage='Nothing to display.' />
        </p>
      </div>
    )
  }
}
