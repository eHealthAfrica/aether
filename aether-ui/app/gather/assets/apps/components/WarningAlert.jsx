import React, { Component } from 'react'

/**
 * WarningAlert component.
 *
 * Renders a list of alert messages indicating the warnings that happened
 * while executing any action.
 */

export default class WarningAlert extends Component {
  render () {
    const {warnings} = this.props
    if (!warnings || !warnings.length) {
      return <div />
    }

    return (
      <div data-qa='data-warning' className='form-warning'>
        {
          warnings.map((warning, index) => (
            <p className='warning' key={index}>
              { warning }
            </p>
          ))
        }
      </div>
    )
  }
}
