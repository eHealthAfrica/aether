import React, { Component } from 'react'
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'

import { clone, deepEqual } from '../utils'
import { deleteData, postData, putData } from '../utils/request'

import { ConfirmButton, ErrorAlert, HelpMessage } from '../components'

const MESSAGES = defineMessages({
  addTitle: {
    defaultMessage: 'New survey',
    id: 'survey.form.title.add'
  },
  editTitle: {
    defaultMessage: 'Edit survey “{name}”',
    id: 'survey.form.title.edit'
  },

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
    const {formatMessage} = this.props.intl

    const survey = this.state
    const isNew = (survey.id === undefined)
    const title = (
      isNew
      ? formatMessage(MESSAGES.addTitle)
      : formatMessage(MESSAGES.editTitle, {...this.props.survey})
    )
    const dataQA = (
      isNew
      ? 'survey-add'
      : `survey-edit-${survey.id}`
    )

    return (
      <div data-qa={dataQA} className='survey-edit'>
        <h3 className='page-title'>{title}</h3>

        <ErrorAlert errors={survey.errors.global} />

        <form onSubmit={this.onSubmit.bind(this)} encType='multipart/form-data'>
          <div className='form-group big-input'>
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
            <ErrorAlert errors={survey.errors.name} />
          </div>

          <div className='form-group big-input'>
            <label className='form-control-label title'>
              <FormattedMessage
                id='survey.form.schema'
                defaultMessage='JSON Schema' />
            </label>
            <HelpMessage>
              <FormattedMessage
                id='survey.form.schema.help'
                defaultMessage='You can type or paste the JSON schema here, or upload a file using the button below.' />
              <br />
              <a href='http://json-schema.org/examples.html' target='_blank'>
                <FormattedMessage
                  id='survey.form.schema.json.link'
                  defaultMessage='Click here to see more about JSON Schema' />
              </a>
            </HelpMessage>
            <textarea
              name='schemaStringified'
              className='form-control'
              rows={10}
              value={survey.schemaStringified}
              onChange={this.onInputChange.bind(this)}
            />
            <ErrorAlert errors={survey.errors.schema} />
          </div>

          <div className='form-group big-input'>
            <label className='form-control-label title'>
              <FormattedMessage
                id='survey.form.schema.file'
                defaultMessage='Schema file' />
            </label>
            <HelpMessage>
              <FormattedMessage
                id='survey.form.schema.file.help'
                defaultMessage='You can also upload a file instead of entering the JSON schema manually' />
            </HelpMessage>
            <input
              name='schemaFile'
              type='file'
              className='form-control'
              accept='.json'
              onChange={this.onFileChange.bind(this)}
            />
            <ErrorAlert errors={survey.errors.schema_file} />
          </div>

          <div className='actions'>

            { !isNew &&
              <div>
                <ConfirmButton
                  className='btn btn-delete'
                  cancelable
                  onConfirm={this.onDelete.bind(this)}
                  title={title}
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
                title={title}
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
        </form>
      </div>
    )
  }

  onInputChange (event) {
    event.preventDefault()
    this.setState({ [event.target.name]: event.target.value })
  }

  onFileChange (event) {
    event.preventDefault()
    this.setState({ [event.target.name]: event.target.files[0] })
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
      console.log(e)
      // let's suppose that the `schemaStringified` is wrong because it was modified
      return true
    }
  }

  onCancel () {
    if (this.state.id) {
      // navigate to Survey view page
      window.location.pathname = `/surveys/view/${this.state.id}`
    } else {
      // navigate to Surveys list page
      window.location.pathname = '/surveys/list/'
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

    const saveMethod = (this.state.id ? putData : postData)
    const url = '/core/surveys' + (this.state.id ? '/' + this.state.id : '') + '.json'

    return saveMethod(url, survey, multipart)
      .then(response => {
        if (response.id) {
          // navigate to Surveys view page
          window.location.pathname = `/surveys/view/${response.id}`
        } else {
          // navigate to Surveys list page
          window.location.pathname = '/surveys/list/'
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
    const survey = this.state

    return deleteData(`/core/surveys/${survey.id}.json`)
      .then(() => {
        // navigate to Surveys list page
        window.location.pathname = '/surveys/list/'
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
