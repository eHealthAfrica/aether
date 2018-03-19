import React, {Component} from 'react'
import { FormattedMessage } from 'react-intl'

/**
 * ConfirmButton component.
 *
 * Renders a button that will trigger a (conditional) Confirm Window
 * to continue executing the expected action.
 */

export default class ConfirmButton extends Component {
  constructor (props) {
    super(props)
    this.state = { open: false }
  }

  render () {
    if (!this.state.open) {
      return (
        <button
          type='button'
          className={this.props.className || 'btn btn-primary'}
          onClick={this.onClick.bind(this)}>
          { this.props.buttonLabel || this.props.title }
        </button>
      )
    }

    return (
      <div className='confirmation-container'>
        { /* show disabled button */ }
        <button
          type='button'
          disabled
          className={this.props.className || 'btn btn-primary'}>
          { this.props.buttonLabel || this.props.title }
        </button>

        <div className='modal show'>
          <div className='modal-dialog modal-md'>
            <div className='modal-content'>
              <div className='modal-header'>
                <h5 className='modal-title'>{this.props.title}</h5>
                <button
                  type='button'
                  className='close'
                  onClick={this.onCancel.bind(this)}>
                  &times;
                </button>
              </div>

              <div className='modal-body'>
                {this.props.message}
              </div>

              <div className='modal-footer'>
                { this.props.cancelable &&
                  <button
                    type='button'
                    className='btn btn-default'
                    onClick={this.onCancel.bind(this)}>
                    <FormattedMessage
                      id='confirm.button.action.cancel'
                      defaultMessage='No' />
                  </button>
                }
                <button
                  type='button'
                  className='btn btn-secondary'
                  onClick={this.execute.bind(this)}>
                  <FormattedMessage
                    id='confirm.button.action.confirm'
                    defaultMessage='Yes' />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  onCancel () {
    this.setState({ open: false })
  }

  onClick () {
    // if there is a condition but it is not satisfied
    if (this.props.condition && !this.props.condition()) {
      this.execute()
      return
    }

    // show modal
    this.setState({ open: true })
  }

  execute () {
    this.setState({ open: false }, this.props.onConfirm)
  }
}
