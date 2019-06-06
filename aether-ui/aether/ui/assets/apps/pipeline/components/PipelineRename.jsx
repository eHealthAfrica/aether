import React, { Component } from 'react'
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'

const MESSAGES = defineMessages({
  namePlaceholder: {
    defaultMessage: 'Name of pipeline',
    id: 'pipeline.rename.placeholder'
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
    return this.props.view !== 'form' ? (
      <span className='pipeline-name'>
        // { this.props.name }
      </span>
    ) : this.renderForm()
  }

  renderForm () {
    const { formatMessage } = this.props.intl

    const onSubmit = (event) => {
      event.preventDefault()
      this.props.onSave(this.state.name)
    }

    return (
      <form className='pipeline-form' onSubmit={onSubmit}>
        <div className='form-group'>
          <input
            type='text'
            required
            name='name'
            className='text-input'
            placeholder={formatMessage(MESSAGES.namePlaceholder)}
            value={this.state.name}
            onChange={event => { this.setState({ name: event.target.value }) }}
          />
        </div>

        <button
          type='button'
          className='btn btn-c btn-big btn-transparent'
          onClick={() => this.props.onCancel()}>
          <span className='details-title'>
            <FormattedMessage
              id='pipeline.rename.button.cancel'
              defaultMessage='Cancel'
            />
          </span>
        </button>

        <button
          type='submit'
          className='btn btn-c btn-big'>
          <span className='details-title'>
            <FormattedMessage
              id='pipeline.rename.button.ok'
              defaultMessage='Save'
            />
          </span>
        </button>
      </form>
    )
  }
}

export default injectIntl(PipelineRename)
