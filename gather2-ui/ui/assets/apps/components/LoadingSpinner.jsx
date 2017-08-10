import React from 'react'

export default class LoadingSpinner extends React.Component {
  render () {
    return (
      <div data-qa='data-loading' className='container-fluid'>
        <p className='alert alert-info'>
          <i className='loading-spinner' />
          Loading data from server…
        </p>
      </div>
    )
  }
}
