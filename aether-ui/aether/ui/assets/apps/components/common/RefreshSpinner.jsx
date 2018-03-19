import React, { Component } from 'react'

/**
 * RefreshSpinner component.
 *
 * Renders a spinner that overlays the current page.
 */

export default class RefreshSpinner extends Component {
  render () {
    return (
      <div data-qa='data-refreshing' className='refreshing'>
        <div className='loading-spinner' />
      </div>
    )
  }
}
