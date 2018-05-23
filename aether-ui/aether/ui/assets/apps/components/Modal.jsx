import React, { Component } from 'react'
import { injectIntl, FormattedMessage } from 'react-intl'

class Modal extends Component {
  render () {
    return (
      <div className={`modal ${this.props.show && 'show'}`}>
        <div className='modal-dialog'>
          <div className='modal-header'>
            <span>{this.props.header}</span>
          </div>
          <div className='modal-content'>
            {this.props.children}
            <br />
            <div className='modal-actions'>
              <button type='button' className='btn btn-w' onClick={this.props.onClose}>
                <FormattedMessage
                  id='publish.modal.cancel'
                  defaultMessage='Cancel'
                />
              </button>
              {this.props.buttons}
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export default injectIntl(Modal)
