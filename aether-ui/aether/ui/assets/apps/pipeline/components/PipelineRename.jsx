import React, { Component } from 'react'
import { defineMessages, injectIntl, FormattedMessage, FormattedHTMLMessage } from 'react-intl'
import { Modal } from '../../components'

const MESSAGES = defineMessages({
  namePlaceholder: {
    defaultMessage: 'Name of pipeline',
    id: 'rename.modal.name.placeholder'
  },
  header: {
    defaultMessage: 'Rename pipeline <b>{name}</b>',
    id: 'rename.modal.header'
  }
})

class PipelineRename extends Component {
  constructor (props) {
    super(props)
    this.state = {
      name: props.name || ''
    }
  }

  render () {
    const { formatMessage } = this.props.intl

    const onSubmit = (event) => {
      event.preventDefault()
      event.stopPropagation()
      this.props.onSave(this.state.name)
    }

    const buttons = (
      <div>
        <button
          data-qa='rename.modal.button.cancel'
          className='btn btn-w'
          onClick={this.props.onCancel}>
          <FormattedMessage
            id='rename.modal.button.cancel'
            defaultMessage='Cancel'
          />
        </button>

        <button className='btn btn-w btn-primary' onClick={onSubmit}>
          <FormattedMessage
            id='rename.modal.button.save'
            defaultMessage='Save'
          />
        </button>
      </div>
    )

    return (
      <Modal
        buttons={buttons}
        header={
          <FormattedHTMLMessage
            {
            ...{
              ...MESSAGES.header,
              values: {
                name: this.props.name
              }
            }
            }
          />
        }
      >
        <form>
          <div className='form-group'>
            <label className='form-label'>
              <FormattedMessage
                id='rename.modal.name.label'
                defaultMessage='Pipeline name'
              />
            </label>
            <input
              type='text'
              required
              name='name'
              className='text-input input-large'
              placeholder={formatMessage(MESSAGES.namePlaceholder)}
              value={this.state.name}
              onChange={event => { this.setState({ name: event.target.value }) }}
            />
          </div>
        </form>
      </Modal>
    )
  }
}

export default injectIntl(PipelineRename)
