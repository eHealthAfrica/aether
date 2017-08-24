import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

export default class EmptyAlert extends Component {
  render () {
    return (
      <div data-qa='data-empty' className='container-fluid'>
        <p className='alert alert-danger'>
          <i className='fa fa-warning' />
          &nbsp;
          <FormattedMessage
            id='alert.empty'
            defaultMessage='Nothing to display.' />
        </p>
      </div>
    )
  }
}
