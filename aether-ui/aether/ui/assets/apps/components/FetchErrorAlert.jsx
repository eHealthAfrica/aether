import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

/**
 * FetchErrorAlert component.
 *
 * Renders an alert message indicating that an error happened
 * while requesting data from server.
 */

export default class FetchErrorAlert extends Component {
  render () {
    return (
      <div data-qa='data-erred' className='container-fluid'>
        <p className='alert alert-danger'>
          <i className='fa fa-warning mr-1' />
          <FormattedMessage
            id='alert.error.fetch'
            defaultMessage={`
              Request was not successful, maybe requested resource does
              not exists or there was a server error while requesting for it.
            `} />
        </p>
      </div>
    )
  }
}
