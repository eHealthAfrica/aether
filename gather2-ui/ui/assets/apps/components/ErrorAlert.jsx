import React, { Component } from 'react'

export default class ErrorAlert extends Component {
  render () {
    const {errors} = this.props
    if (!errors || !errors.length) {
      return <div />
    }

    return (
      <div data-qa='data-erred' className='form-error'>
        {
          errors.map((error, index) => (
            <p className='error' key={index}>
              { error }
            </p>
          ))
        }
      </div>
    )
  }
}
