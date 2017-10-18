import React, { Component } from 'react'

/**
 * ErrorAlert component.
 *
 * Renders a list of alert messages indicating the errors that happened
 * while executing any action.
 */

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
