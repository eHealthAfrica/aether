import React, { Component } from 'react'

/**
 * HelpMessage component.
 *
 * Renders a question button that shows/hides a help message.
 */

export default class HelpMessage extends Component {
  render () {
    const randomId = `help-content-${Math.random().toString(36).slice(2)}`

    return (
      <div data-qa='data-help-message' className='d-inline'>
        <button
          type='button'
          className='btn btn-sm btn-info rounded-circle float-right'
          data-toggle='collapse'
          data-target={'#' + randomId}>
          <i className='fa fa-question' />
        </button>
        <div className='collapse' id={randomId}>
          <div className='help-container'>
            { this.props.children }
          </div>
        </div>
      </div>
    )
  }
}
