import React, { Component } from 'react'

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
