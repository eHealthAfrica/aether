import React, { Component } from 'react'

export default class ErrorAlert extends Component {
  render () {
    const {errors} = this.props
    if (!errors || !errors.length) {
      return <div />
    }

    return (
      <div data-qa='data-erred'>
        {
          errors.map((error, index) => (
            <p className='badge badge-danger' key={index}>
              <i className='fa fa-warning mr-1' />
              { error }
            </p>
          ))
        }
      </div>
    )
  }
}
