import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

export default class LoadingSpinner extends Component {
  render () {
    return (
      <div data-qa='data-loading' className='container-fluid'>
        <p className='alert alert-info'>
          <i className='loading-spinner mr-1' />
          <FormattedMessage
            id='alert.loading'
            defaultMessage='Loading data from server…' />
        </p>
      </div>
    )
  }
}
