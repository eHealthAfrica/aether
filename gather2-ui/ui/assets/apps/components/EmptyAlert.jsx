import React from 'react'

export default class EmptyAlert extends React.Component {
  render () {
    return (
      <div data-qa='data-empty' className='container-fluid'>
        <p className='alert alert-danger'>
          <i className='fa fa-warning' />
          &nbsp;
          Nothing to display.
        </p>
      </div>
    )
  }
}
