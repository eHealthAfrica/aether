import React from 'react'

export default class FetchErrorAlert extends React.Component {
  render () {
    return (
      <div data-qa='data-erred' className='container-fluid'>
        <p className='alert alert-danger'>
          <i className='fa fa-warning' />
          &nbsp;
          Request was not successful, maybe requested resource does
          not exists or there was a server error while requesting for it.
        </p>
      </div>
    )
  }
}
