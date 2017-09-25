import React, { Component } from 'react'
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'

import { clone, deepEqual } from '../utils'
import { deleteData, postData, putData } from '../utils/request'
import { getSurveysAPIPath, getSurveysPath } from '../utils/paths'

import { ConfirmButton, ErrorAlert, HelpMessage } from '../components'

const MESSAGES = defineMessages({
  schemaError: {
    defaultMessage: 'This is not a valid JSON schema.',
    id: 'survey.form.schema.error'
  },

  cancelButton: {
    defaultMessage: 'Cancel',
    id: 'survey.form.action.cancel'
  },
  cancelConfirm: {
    defaultMessage: 'Are you sure you want to cancel your changes?',
    id: 'survey.form.action.cancel.confirm'
  },

  deleteButton: {
    defaultMessage: 'Delete survey',
    id: 'survey.form.action.delete'
  },
  deleteConfirm: {
    defaultMessage: 'Are you sure you want to delete the survey “{name}”?',
    id: 'survey.form.action.delete.confirm'
  },
  deleteError: {
    defaultMessage: 'An error occurred while deleting “{name}”',
    id: 'survey.form.action.delete.error'
  },
  submitError: {
    defaultMessage: 'An error occurred while saving “{name}”',
    id: 'survey.form.action.submit.error'
  }
})

export class SurveyForm extends Component {
  constructor (props) {
    super(props)
    this.state = {
      ...clone(this.props.survey),
      schemaStringified: JSON.stringify(this.props.survey.schema || {}, 0, 2),
      errors: {}
    }
  }

  render () {
    const survey = this.state
    const {errors} = survey
    const dataQA = (
      (survey.id === undefined)
      ? 'survey-add'
      : `survey-edit-${survey.id}`
    )

    return (
      <div data-qa={dataQA} className='survey-edit'>
        <h3 className='page-title'>{ this.renderTitle() }</h3>

        <ErrorAlert errors={errors.global} />

        <form onSubmit={this.onSubmit.bind(this)} encType='multipart/form-data'>
          { this.renderName() }
          { this.renderJSONSchema() }
          { this.renderButtons() }
        </form>
      </div>
    )
  }

  renderTitle () {
    const survey = this.state
    if (survey.id === undefined) {
      return (
        <FormattedMessage
          id='survey.form.title.add'
          defaultMessage='New survey' />
      )
    } else {
      return (
        <span>
          <FormattedMessage
            id='survey.form.title.edit'
            defaultMessage='Edit survey' />
          <b className='ml-2'>{survey.name}</b>
        </span>
      )
    }
  }

  renderName () {
    const survey = this.state
    const {errors} = survey

    return (
      <div className={`form-group big-input ${errors.name ? 'error' : ''}`}>
        <label className='form-control-label title'>
          <FormattedMessage
            id='survey.form.name'
            defaultMessage='Survey name' />
        </label>
        <input
          name='name'
          type='text'
          className='form-control'
          required
          value={survey.name || ''}
          onChange={this.onInputChange.bind(this)}
        />
        <ErrorAlert errors={errors.name} />
      </div>
    )
  }

  renderJSONSchema () {
    const survey = this.state
    const {errors} = survey

    return (
      <div>
        <div className={`form-group big-input ${errors.schema || errors.schema_file ? 'error' : ''}`}>
          <label className='form-control-label title'>
            <FormattedMessage
              id='survey.form.schema'
              defaultMessage='JSON Schema' />
          </label>
          <HelpMessage>
            <FormattedMessage
              id='survey.form.schema.help'
              defaultMessage='You can upload a file using the button below or type or paste the JSON schema in the textarea.' />
            <br />
            <a href='http://json-schema.org/examples.html' target='_blank'>
              <FormattedMessage
                id='survey.form.schema.json.link'
                defaultMessage='Click here to see more about JSON Schema' />
            </a>
          </HelpMessage>
        </div>

        <div className={`form-group big-input ${errors.schema_file ? 'error' : ''}`}>
          <label className='btn btn-info' htmlFor='schemaFile'>
            <FormattedMessage
              id='survey.form.schema.file'
              defaultMessage='Choose JSON schema file' />
          </label>
          <input
            name='schemaFile'
            id='schemaFile'
            type='file'
            className='hidden-file'
            accept='.json'
            onChange={this.onFileChange.bind(this)}
          />
          {
            survey.schemaFile &&
            <span className='ml-4'>
              <i>{ survey.schemaFile.name }</i>
              <button
                className='btn btn-sm btn-danger ml-2'
                onClick={this.removeFile.bind(this)}>&times;</button>
            </span>
          }
          <ErrorAlert errors={errors.schema_file} />
        </div>

        <div className={`form-group big-input ${errors.schema ? 'error' : ''}`}>
          <textarea
            name='schemaStringified'
            className='form-control code'
            disabled={survey.schemaFile !== undefined}
            rows={10}
            value={survey.schemaStringified}
            onChange={this.onInputChange.bind(this)}
          />
          <ErrorAlert errors={errors.schema} />
        </div>
      </div>
    )
  }

  renderButtons () {
    const {formatMessage} = this.props.intl

    return (
      <div className='actions'>
        { (this.props.survey.id !== undefined) &&
          <div>
            <ConfirmButton
              className='btn btn-delete'
              cancelable
              onConfirm={this.onDelete.bind(this)}
              title={this.renderTitle()}
              message={formatMessage(MESSAGES.deleteConfirm, {...this.props.survey})}
              buttonLabel={formatMessage(MESSAGES.deleteButton)}
            />
          </div>
        }
        <div>
          <ConfirmButton
            className='btn btn-cancel btn-block'
            cancelable
            condition={this.onCancelCondition.bind(this)}
            onConfirm={this.onCancel.bind(this)}
            title={this.renderTitle()}
            message={formatMessage(MESSAGES.cancelConfirm)}
            buttonLabel={formatMessage(MESSAGES.cancelButton)}
          />
        </div>
        <div>
          <button type='submit' className='btn btn-primary btn-block'>
            <FormattedMessage
              id='survey.form.action.submit'
              defaultMessage='Save survey' />
          </button>
        </div>
      </div>
    )
  }

  onInputChange (event) {
    event.preventDefault()
    this.setState({ [event.target.name]: event.target.value })
  }

  onFileChange (event) {
    event.preventDefault()
    this.setState({ [event.target.name]: event.target.files.item(0) })
  }

  removeFile (event) {
    event.preventDefault()
    this.setState({ schemaFile: undefined })
  }

  onCancelCondition () {
    // check if there were changes
    if (this.state.schemaFile !== undefined) {
      return true
    }

    try {
      const survey = {
        ...clone(this.props.survey),
        name: this.state.name,
        schema: JSON.parse(this.state.schemaStringified)
      }

      return !deepEqual(this.props.survey, survey, true)
    } catch (e) {
      // let's suppose that the `schemaStringified` is wrong because it was modified
      return true
    }
  }

  onCancel () {
    if (this.props.survey.id) {
      // navigate to Survey view page
      window.location.pathname = getSurveysPath({action: 'view', id: this.props.survey.id})
    } else {
      // navigate to Surveys list page
      window.location.pathname = getSurveysPath({action: 'list'})
    }
  }

  onSubmit (event) {
    event.preventDefault()
    this.setState({ errors: {} })

    const {formatMessage} = this.props.intl
    const survey = {
      id: this.state.id,
      name: this.state.name
    }

    // check if the schema comes from a file or from the textarea
    const {schemaFile, schemaStringified} = this.state
    let multipart = false
    if (schemaFile) {
      multipart = true
      survey.schema = '{}'
      survey.schema_file = schemaFile
    } else {
      try {
        survey.schema = JSON.parse(schemaStringified)
      } catch (e) {
        this.setState({
          errors: {
            schema: [formatMessage(MESSAGES.schemaError)]
          }
        })
        return
      }
    }

    const saveMethod = (survey.id ? putData : postData)
    const url = getSurveysAPIPath({id: survey.id})

    return saveMethod(url, survey, multipart)
      .then(response => {
        if (response.id) {
          // navigate to Surveys view page
          window.location.pathname = getSurveysPath({action: 'view', id: response.id})
        } else {
          // navigate to Surveys list page
          window.location.pathname = getSurveysPath({action: 'list'})
        }
      })
      .catch(error => {
        console.log(error.message)
        error.response
          .then(resp => {
            this.setState({ errors: resp })
          })
          .catch(() => {
            this.setState({
              errors: {
                global: [formatMessage(MESSAGES.submitError, {...survey})]
              }
            })
          })
      })
  }

  onDelete () {
    const {formatMessage} = this.props.intl
    const {survey} = this.props

    return deleteData(getSurveysAPIPath({id: survey.id}))
      .then(() => {
        // navigate to Surveys list page
        window.location.pathname = getSurveysPath({action: 'list'})
      })
      .catch(error => {
        console.log(error.message)
        this.setState({
          errors: {
            global: [formatMessage(MESSAGES.deleteError, {...survey})]
          }
        })
      })
  }
}

// Include this to enable `this.props.intl` for this component.
export default injectIntl(SurveyForm)
