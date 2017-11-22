import React, { Component } from 'react'
import {
  defineMessages,
  injectIntl,
  FormattedMessage
} from 'react-intl'

import { clone } from '../utils'
import {
  ConfirmButton,
  ErrorAlert,
  FullDateTime,
  HelpMessage,
  MultiSelect
} from '../components'

const MESSAGES = defineMessages({
  newForm: {
    defaultMessage: 'new',
    id: 'survey.odk.form.xform.new'
  },
  description: {
    defaultMessage: 'Write optional xForm description…',
    id: 'survey.odk.form.xform.description.placeholder'
  },
  deleteConfirm: {
    defaultMessage: 'Are you sure you want to delete the xForm “{title}”?',
    id: 'survey.odk.form.xform.action.delete.confirm'
  }
})

export class SurveyODKForm extends Component {
  constructor (props) {
    super(props)

    let xforms = [...(props.survey.xforms || [])].map(xform => ({...xform, key: xform.id}))
    xforms.sort((a, b) => (
      (a.title > b.title) ||
      (a.title === b.title && a.created_at > b.created_at)
    )) // sort by title + created_at

    this.state = {
      xforms,
      surveyors: [...(props.survey.surveyors || [])],
      availableSurveyors: clone(props.surveyors.results || [])
    }
  }

  componentDidUpdate (prevProps, prevState) {
    if (prevState !== this.state) {
      this.props.onChange({
        surveyors: [...this.state.surveyors],
        xforms: [...this.state.xforms]
      })
    }
  }

  render () {
    const dataQA = (
      (!this.props.survey.survey_id)
      ? 'survey-odk-add'
      : `survey-odk-edit-${this.props.survey.survey_id}`
    )

    return (
      <div data-qa={dataQA}>
        { this.renderODK() }
        { this.renderSurveyors() }
        { this.renderXForms() }
      </div>
    )
  }

  renderODK () {
    return (
      <div className='survey-section'>
        <label>
          <FormattedMessage
            id='survey.odk.form.odk'
            defaultMessage='ODK Collect' />
        </label>
        <HelpMessage>
          <FormattedMessage
            id='survey.odk.form.odk.help.odk'
            defaultMessage='Open Data Kit (ODK) is a free and open-source set of tools which help organizations author, field, and manage mobile data collection solutions.' />
          <br />
          <a href='https://opendatakit.org/' target='_blank'>
            <FormattedMessage
              id='survey.odk.form.odk.help.odk.link'
              defaultMessage='Click here to see more about Open Data Kit' />
          </a>
        </HelpMessage>
      </div>
    )
  }

  renderSurveyors () {
    const errors = this.props.errors || {}
    const {surveyors, availableSurveyors} = this.state
    const selectedSurveyors = availableSurveyors.filter(surveyor => surveyors.indexOf(surveyor.id) > -1)
    const onChange = (surveyors) => this.setState({
      surveyors: surveyors.map(surveyor => surveyor.id)
    })

    return (
      <div className={`form-group ${errors.surveyors ? 'error' : ''}`}>
        <label className='form-control-label title'>
          <FormattedMessage
            id='survey.odk.form.surveyors'
            defaultMessage='Granted Surveyors' />
        </label>
        <MultiSelect
          values={selectedSurveyors}
          options={availableSurveyors}
          valueProp='id'
          textProp='username'
          onChange={onChange}
        />
        <ErrorAlert errors={errors.surveyors} />
      </div>
    )
  }

  renderXForms () {
    const {xforms, surveyors} = this.state

    return (
      <div>
        <div>
          <label className='form-control-label title'>
            <FormattedMessage
              id='survey.odk.form.xforms.list'
              defaultMessage='xForms' />
          </label>
          <HelpMessage>
            <FormattedMessage
              id='survey.odk.form.xform.file.help'
              defaultMessage='XLSForm is a kind of survey definition used by ODK Collect.' />
            <br />
            <a href='http://xlsform.org/' target='_blank'>
              <FormattedMessage
                id='survey.odk.form.odk.help.xlsform.link'
                defaultMessage='Click here to see more about XLSForm' />
            </a>
          </HelpMessage>
        </div>

        <div className='form-items'>
          {
            xforms.map((xform, index) => (
              <XLSFormIntl
                key={xform.key}
                xform={xform}
                surveyors={surveyors}
                onRemove={() => this.setState({
                  xforms: xforms.filter((_, jndex) => jndex !== index)
                })}
                onChange={(changedXForm) => this.setState({
                  xforms: [
                    ...xforms.filter((_, jndex) => jndex < index),
                    changedXForm,
                    ...xforms.filter((_, jndex) => jndex > index)
                  ]
                })}
              />
            ))
          }
        </div>
        <div className='form-group mt-4'>
          <label className='btn btn-secondary' htmlFor='xFormFiles'>
            <FormattedMessage
              id='survey.odk.form.xforms.file'
              defaultMessage='Add xForm / XLSForm files' />
          </label>
          <input
            name='files'
            id='xFormFiles'
            type='file'
            multiple
            className='hidden-file'
            accept='.xls,.xlsx,.xml'
            onChange={this.onFileChange.bind(this)}
          />
        </div>
      </div>
    )
  }

  onFileChange (event) {
    event.preventDefault()
    const xforms = []
    const {formatMessage} = this.props.intl

    // https://developer.mozilla.org/en-US/docs/Web/API/FileList
    for (let i = 0; i < event.target.files.length; i++) {
      const file = event.target.files.item(i)
      xforms.push({
        key: Math.random().toString(36).slice(2),
        title: file.name,
        form_id: formatMessage(MESSAGES.newForm),
        file
      })
    }

    this.setState({ xforms: [ ...this.state.xforms, ...xforms ] })
  }
}

class XLSForm extends Component {
  constructor (props) {
    super(props)

    this.state = {
      ...clone(this.props.xform),
      editView: false
    }
  }

  componentDidUpdate (prevProps, prevState) {
    if (prevState !== this.state) {
      this.props.onChange(this.state)
    }
  }

  render () {
    const {formatMessage} = this.props.intl
    const xform = this.state

    const title = (
      <span title={xform.description}>
        {xform.title}
        <span className='badge badge-default ml-2'>{xform.form_id}</span>
      </span>
    )

    return (
      <div className={`form-item mb-2 ${this.state.editView ? 'expanded' : ''}`}>
        <i className='fa fa-file mr-2' />
        { title }
        <small className='ml-2'>
          <FullDateTime date={xform.created_at} />
        </small>
        <ConfirmButton
          className='btn btn-sm icon-only btn-danger ml-2 mr-2'
          cancelable
          onConfirm={this.props.onRemove}
          title={title}
          message={formatMessage(MESSAGES.deleteConfirm, {...xform})}
          buttonLabel={<i className='fa fa-close' />}
        />

        { /* only existing xforms can edit */
          xform.id &&
          <button
            className='btn btn-sm btn-secondary btn-edit icon-only'
            onClick={this.toggleEditView.bind(this)}>
            <i className={`fa fa-${this.state.editView ? 'minus' : 'pencil'}`} />
          </button>
        }

        {
          this.state.editView &&
          <div className='edit-form-item mt-3'>
            <div className='form-group'>
              <textarea
                name='description'
                className='form-control code mb-2'
                rows={3}
                value={xform.description}
                placeholder={formatMessage(MESSAGES.description)}
                onChange={this.onInputChange.bind(this)}
              />

              <label className='btn btn-secondary' htmlFor='xFormFile'>
                <FormattedMessage
                  id='survey.odk.form.xform.file'
                  defaultMessage='Upload new xForm/XLSForm file' />
              </label>
              <input
                name='file'
                id='xFormFile'
                type='file'
                className='hidden-file'
                accept='.xls,.xlsx,.xml'
                onChange={this.onFileChange.bind(this)}
              />
              {
                xform.file &&
                <span className='ml-4'>
                  <span>{ xform.file.name }</span>
                  <button
                    className='btn btn-sm icon-only btn-danger ml-2'
                    onClick={this.removeFile.bind(this)}><i className='fa fa-close' /></button>
                </span>
              }

              <textarea
                name='xml_data'
                className='form-control code'
                disabled={xform.file !== undefined}
                rows={10}
                value={xform.xml_data}
                onChange={this.onInputChange.bind(this)}
              />
            </div>
          </div>
        }
      </div>
    )
  }

  toggleEditView (event) {
    event.preventDefault()
    this.setState({ editView: !this.state.editView })
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
    this.setState({ file: undefined })
  }
}

// Include this to enable `this.props.intl` for this component.
export default injectIntl(SurveyODKForm)
const XLSFormIntl = injectIntl(XLSForm)
