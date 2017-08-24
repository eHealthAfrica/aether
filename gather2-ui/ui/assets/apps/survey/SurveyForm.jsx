import React, { Component } from 'react'
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'

import { deepEqual } from '../utils'

const MESSAGES = defineMessages({
  addTitle: {
    defaultMessage: 'New survey',
    id: 'survey.form.title.add'
  },
  editTitle: {
    defaultMessage: 'Edit survey “{name}”',
    id: 'survey.form.title.edit'
  },
  cancelConfirm: {
    defaultMessage: 'Are you sure you want to cancel your changes?',
    id: 'survey.form.action.cancel.confirm'
  }
})

export class SurveyForm extends Component {
  constructor (props) {
    super(props)
    this.state = this.props.survey
  }

  render () {
    const {formatMessage} = this.props.intl

    const survey = this.state
    const title = (
      survey.id
      ? formatMessage(MESSAGES.editTitle, {...this.props.survey})
      : formatMessage(MESSAGES.addTitle)
    )
    const dataQA = (
      survey.id
      ? `survey-edit-${survey.id}`
      : 'survey-add'
    )

    return (
      <div data-qa={dataQA} className='survey-edit'>
        <h3>{title}</h3>

        <form onSubmit={() => console.log('TBD')}>
          <div className='form-group big-input'>
            <label className='form-control-label title'>
              <FormattedMessage
                id='survey.form.name'
                defaultMessage='Survey name' />
            </label>
            <input
              type='text'
              className='form-control'
              required
              value={survey.name || ''}
              onChange={this.onNameChange.bind(this)}
            />
          </div>

          <div className='row actions'>
            <div className='col-sm-9'>
              <button
                type='button'
                className='btn btn-cancel pull-right col-sm-4'
                onClick={this.onCancel.bind(this)}>
                <FormattedMessage
                  id='survey.form.action.cancel'
                  defaultMessage='Cancel' />
              </button>
            </div>
            <div className='col-sm-3'>
              <button type='submit' className='btn btn-primary btn-block'>
                <FormattedMessage
                  id='survey.form.action.submit'
                  defaultMessage='Save survey' />
              </button>
            </div>
          </div>
        </form>
      </div>
    )
  }

  onNameChange (e) {
    this.setState({ name: e.target.value })
  }

  onCancel (event) {
    event.preventDefault()

    const {formatMessage} = this.props.intl

    // check if there were changes
    let shouldCancel = true
    if (!deepEqual(this.props.survey, this.state, true)) {
      shouldCancel = window.confirm(formatMessage(MESSAGES.cancelConfirm))
    }

    if (shouldCancel) {
      if (this.state.id) {
        // navigate to Survey view page
        window.location.pathname = `/surveys/view/${this.state.id}`
      } else {
        // navigate to Surveys list page
        window.location.pathname = '/surveys/list/'
      }
    }
  }
}

// Include this to enable `this.props.intl` for this component.
export default injectIntl(SurveyForm)
