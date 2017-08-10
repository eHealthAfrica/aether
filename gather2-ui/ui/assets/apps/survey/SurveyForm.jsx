import React, { Component } from 'react'

import { deepEqual } from '../utils'

export default class SurveyForm extends Component {
  constructor (props) {
    super(props)
    this.state = this.props.survey
  }

  render () {
    const survey = this.state
    const title = (survey.id ? `Edit survey: ${this.props.survey.name}` : 'New survey')

    return (
      <div className='survey-edit' data-qa='edit-survey'>
        <h3>{title}</h3>

        <form onSubmit={() => console.log('TBD')}>
          <div className='form-group big-input'>
            <label className='form-control-label title'>Survey name</label>
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
                Cancel
              </button>
            </div>
            <div className='col-sm-3'>
              <button type='submit' className='btn btn-primary btn-block'>
                Save Survey
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

    // check if there were changes
    let shouldCancel = true
    if (!deepEqual(this.props.survey, this.state, true)) {
      shouldCancel = window.confirm('Are you sure you want to cancel your changes?')
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
