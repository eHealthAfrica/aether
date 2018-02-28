import React, { Component } from 'react'
import {
  defineMessages,
  injectIntl,
  FormattedMessage,
  FormattedRelative
} from 'react-intl'

import { clone } from '../utils'
import {
  ConfirmButton,
  ErrorAlert,
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
  },
  deleteMediaConfirm: {
    defaultMessage: 'Are you sure you want to delete the media file “{name}”?',
    id: 'survey.odk.form.xform.media.file.action.delete.confirm'
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
        ...this.props.survey,
        surveyors: [...this.state.surveyors],
        xforms: [...this.state.xforms]
      })
    }
  }

  render () {
    const dataQA = (!this.props.survey.mapping_id
      ? 'survey-odk-add'
      : `survey-odk-edit-${this.props.survey.mapping_id}`
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
              <XFormIntl
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
        version: formatMessage(MESSAGES.newForm),
        file
      })
    }

    this.setState({ xforms: [ ...this.state.xforms, ...xforms ] })
  }
}

class XForm extends Component {
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
      <span title={xform.description} className='form-title'>
        <i className='fa fa-file mr-2' />
        {xform.title}
        <span className='badge badge-default mx-2'>
          <FormattedMessage
            id='survey.odk.form.xform.version'
            defaultMessage='version'
          />: {xform.version}
        </span>
      </span>
    )

    const mediaFiles = (xform.id
      ? (
        <aside className='mr-3'>
          <span className='badge badge-info mr-1'>
            { xform.media_files.length }
          </span>
          <small>
            <FormattedMessage
              id='survey.odk.form.xform.media.files.count'
              defaultMessage='media files'
            />
          </small>
        </aside>
      )
      : (
        <small className='mx-4'>
          <FormattedMessage
            id='survey.odk.form.xforms.file.media.files'
            defaultMessage='To add media files you need to save the survey first'
          />
        </small>
      )
    )

    const date = (xform.id
      ? <small className='mr-4'>(<FormattedRelative value={xform.created_at} />)</small>
      : ''
    )

    return (
      <div className={`form-item mb-2 ${this.state.editView ? 'expanded' : ''}`}>
        { title }
        { date }
        { mediaFiles }
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

            <MediaFileIntl
              id={xform.id}
              title={title}
              mediaFiles={xform.media_files}
              onChange={(mediaFiles) => this.setState({media_files: mediaFiles})}
            />
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

class MediaFile extends Component {
  constructor (props) {
    super(props)
    this.state = {
      mediaFiles: props.mediaFiles.map(mediaFile => ({...mediaFile, key: mediaFile.name}))
    }
  }

  componentDidUpdate (prevProps, prevState) {
    if (prevState !== this.state) {
      this.props.onChange(this.state.mediaFiles)
    }
  }

  render () {
    const {mediaFiles} = this.state
    const inputFileId = `media-files-${this.props.id}`

    return (
      <div className='mt-4'>
        <FormattedMessage
          id='survey.odk.form.xform.media.files'
          defaultMessage='Media file(s):' />

        {
          mediaFiles.length === 0 &&
          <span className='ml-2'>
            <FormattedMessage
              id='survey.odk.form.xform.media.files.none'
              defaultMessage='None' />
          </span>
        }

        { mediaFiles.map(mediaFile => this.renderMediaFile(mediaFile)) }

        <div className='form-group mt-4 mb-1'>
          <label className='btn btn-secondary' htmlFor={inputFileId}>
            <FormattedMessage
              id='survey.odk.form.xform.media.files.add'
              defaultMessage='Add media files' />
          </label>
          <input
            name='files'
            id={inputFileId}
            type='file'
            multiple
            className='hidden-file'
            onChange={this.onFileChange.bind(this)}
          />
        </div>
      </div>
    )
  }

  renderMediaFile (mediaFile) {
    const {formatMessage} = this.props.intl

    return (
      <span key={mediaFile.id || mediaFile.key} className='ml-2 mb-1 badge badge-info'>
        {
          /*
            This does not work locally with the container name
            but should do in the server. It's possible that the link
            requires authentication... or not.
          */
        }
        <a
          className='btn-link text-white'
          href={mediaFile.media_file || '#'}
          target='_blank'>
          { mediaFile.name }
        </a>

        <ConfirmButton
          className='btn btn-sm icon-only btn-danger ml-2'
          cancelable
          onConfirm={() => this.setState({
            mediaFiles: this.state.mediaFiles.filter(mf => mf.key !== mediaFile.key)
          })}
          title={this.props.title}
          message={formatMessage(MESSAGES.deleteMediaConfirm, {...mediaFile})}
          buttonLabel={<i className='fa fa-close' />}
        />
      </span>
    )
  }

  onFileChange (event) {
    event.preventDefault()
    const mediaFiles = []

    // https://developer.mozilla.org/en-US/docs/Web/API/FileList
    for (let i = 0; i < event.target.files.length; i++) {
      const file = event.target.files.item(i)
      mediaFiles.push({
        key: Math.random().toString(36).slice(2),
        name: file.name,
        file
      })
    }

    this.setState({ mediaFiles: [ ...this.state.mediaFiles, ...mediaFiles ] })
  }
}

// Include this to enable `this.props.intl` for this component.
export default injectIntl(SurveyODKForm)
const XFormIntl = injectIntl(XForm)
const MediaFileIntl = injectIntl(MediaFile)
