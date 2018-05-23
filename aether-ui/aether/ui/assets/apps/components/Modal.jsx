import React, { Component } from 'react'
import { injectIntl } from 'react-intl'

class Modal extends Component {
  render () {
    return (
      <div className={`modal ${this.props.show && 'show'}`}>
        <div className='modal-dialog'>
          <div className='modal-header'>
            <span className='modal-title'>{this.props.header}</span>
          </div>
          <div className='modal-content'>
            {this.props.children}
            <div className='modal-actions'>
              {this.props.buttons}
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export default injectIntl(Modal)
