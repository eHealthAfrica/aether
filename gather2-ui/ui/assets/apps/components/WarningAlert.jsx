import React, { Component } from 'react'

export default class WarningAlert extends Component {
  render () {
    const {warnings} = this.props
    if (!warnings || !warnings.length) {
      return <div />
    }

    return (
      <div data-qa='data-warning'>
        {
          warnings.map((warning, index) => (
            <p className='badge badge-warning' key={index}>
              <i className='fa fa-warning mr-1' />
              { warning }
            </p>
          ))
        }
      </div>
    )
  }
}
