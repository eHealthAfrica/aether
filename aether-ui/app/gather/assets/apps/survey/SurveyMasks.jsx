import React, { Component } from 'react'
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'

import { cleanPropertyName } from '../utils/types'
import { deleteData, postData } from '../utils/request'
import { getMasksAPIPath } from '../utils/paths'
import { ConfirmButton } from '../components'

const MESSAGES = defineMessages({
  namePlaceholder: {
    defaultMessage: 'Mask name',
    id: 'survey.mask.form.name.placeholder'
  }
})

/**
 * SurveyMasks component.
 *
 * Renders the columns selection mask.
 */

export class SurveyMasks extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showColumns: false,
      ...this.buildStateWithProps(props, true)
    }
  }

  componentWillReceiveProps (nextProps) {
    if (nextProps.survey !== this.props.survey ||
      nextProps.columns !== this.props.columns) {
      this.setState({
        ...this.buildStateWithProps(nextProps, (nextProps.columns !== this.props.columns))
      })
    }
  }

  componentDidUpdate (prevProps, prevState) {
    if (prevState.columns !== this.state.columns) {
      const selectedColumns = Object.keys(this.state.columns)
        .filter(key => this.state.columns[key])
      this.props.onChange(selectedColumns)
    }
  }

  buildStateWithProps (props, includeColumns = false) {
    const newState = {
      masks: [
        {
          id: -2,
          name: <FormattedMessage
            id='survey.mask.preset.all'
            defaultMessage='All' />,
          columns: []
        },

        ...props.survey.masks,

        {
          id: -1,
          name: <FormattedMessage
            id='survey.mask.preset.none'
            defaultMessage='None' />,
          columns: [...props.columns]
        }
      ]
    }

    if (includeColumns) {
      newState.columns = {}
      props.columns.forEach(column => { newState.columns[column] = true })
    }

    return newState
  }

  isMaskSelected (mask) {
    const {columns} = this.state
    const keys = Object.keys(columns)
    const length = keys.length

    // check that only the mask columns are selected
    for (let i = 0; i < length; i++) {
      const key = keys[i]
      if (mask.columns.indexOf(key) > -1 && !columns[key]) {
        // in the mask list but not selected
        return false
      }
      if (mask.columns.indexOf(key) === -1 && columns[key]) {
        // not in the mask list but selected
        return false
      }
    }

    return true
  }

  render () {
    const currentMask = this.state.masks.find(mask => this.isMaskSelected(mask)) || {
      id: 0,
      name: <FormattedMessage
        id='survey.mask.preset.custom'
        defaultMessage='Custom' />
    }

    return (
      <div>
        <div className='filter-toggles'>
          <FormattedMessage
            id='survey.mask.fields'
            defaultMessage='Mask fields:' />
          <button
            className={`btn badge ${currentMask.id !== -1 ? 'active' : ''} ${this.state.showColumns ? 'open' : ''} ${currentMask.id > 0 ? 'custom' : ''}`}
            onClick={() => { this.setState({ showColumns: !this.state.showColumns }) }}
          >
            { currentMask.name }
            <i className='fa fa-angle-down ml-2' />
          </button>
        </div>

        { this.renderColumnsMask() }
        { this.renderMessage() }
      </div>
    )
  }

  renderColumnsMask () {
    if (!this.state.showColumns) {
      return <div className='filter-container' />
    }

    return (
      <div className='filter-container active'>
        { this.renderMasksList() }
        { this.renderColumnsList() }

        <button
          className='close-filters'
          onClick={() => { this.setState({ showColumns: false }) }}
        >
          <i className='fa fa-angle-up' />
        </button>
      </div>
    )
  }

  renderMasksList () {
    const getClassName = (mask) => (this.isMaskSelected(mask) ? 'active' : '')
    const selectMaskColumns = (mask) => {
      const columns = {}
      Object.keys(this.state.columns).forEach(key => {
        columns[key] = (mask.columns.indexOf(key) > -1)
      })
      this.setState({ columns })
    }

    return (
      <div className='presets-container'>
        { this.renderForm() }
        <ul className='filter-presets'>
          {
            this.state.masks.map(mask => (
              <li key={mask.id} className={`badge column-preset ${getClassName(mask)} ${mask.id > 0 ? 'custom' : ''}`}>
                <button
                  className='preset-action'
                  onClick={() => selectMaskColumns(mask)}>
                  {mask.name}
                </button>
                {
                  (mask.id > 0) &&
                  <ConfirmButton
                    className='btn btn-sm icon-only preset-delete'
                    title={mask.name}
                    buttonLabel={<i className='fa fa-close' />}
                    cancelable
                    message={
                      <FormattedMessage
                        id='survey.mask.preset.delete.question'
                        defaultMessage='Are you sure you want to delete this mask?'
                      />
                    }
                    onConfirm={() => this.onDelete(mask)}
                  />
                }
              </li>
            ))
          }
        </ul>
      </div>
    )
  }

  renderColumnsList () {
    const toggleColumn = (key) => {
      const columns = {...this.state.columns}
      columns[key] = !columns[key]
      this.setState({ columns })
    }
    const getClassName = (key) => this.state.columns[key] ? 'not-masked' : 'masked'

    return (
      <div className='columns-filter'>
        <ul>
          {
            this.props.columns.map(column => (
              <li
                key={column}
                className={`column-title ${getClassName(column)}`}
                onClick={() => toggleColumn(column)}>
                <div className='marker' />
                <span>
                  { cleanPropertyName(column.split(this.props.separator).join(' - ')) }
                </span>
              </li>
            ))
          }
        </ul>
      </div>
    )
  }

  renderForm () {
    const showForm = this.state.masks
      .filter(mask => this.isMaskSelected(mask))
      .length === 0

    if (!showForm) {
      return
    }

    const {formatMessage} = this.props.intl

    return (
      <div className='save-presets'>
        <form onSubmit={this.onSubmit.bind(this)}>
          <label className='form-control-label title mr-2' htmlFor='mask-name'>
            <FormattedMessage
              id='survey.mask.preset.save.label'
              defaultMessage='Save as' />
          </label>
          <input
            type='text'
            required
            name='name'
            id='mask-name'
            placeholder={formatMessage(MESSAGES.namePlaceholder)}
            className='form-control'
          />
          <button type='submit' className='btn btn-secondary ml-2'>
            <FormattedMessage
              id='survey.mask.preset.save.button'
              defaultMessage='Save' />
          </button>
        </form>
      </div>
    )
  }

  onSubmit (event) {
    event.preventDefault()

    const mask = {
      survey: this.props.survey.mapping_id,
      name: document.getElementById('mask-name').value,
      columns: Object.keys(this.state.columns)
        .filter(key => this.state.columns[key])
    }

    const errorTitle = <FormattedMessage
      id='survey.mask.preset.save.error'
      defaultMessage='Error saving mask' />
    const defaultErrorBody = <FormattedMessage
      id='survey.mask.preset.save.error.unknown'
      defaultMessage='There was an error saving this mask' />

    return postData(getMasksAPIPath({}), mask)
      .then(this.props.reload)
      .catch(error => {
        console.log(error.message)
        error.response
          .then(errors => {
            console.log(errors)
            this.setState({
              message: {
                title: errorTitle,
                body: (errors.non_field_errors
                  ? <FormattedMessage
                    id='survey.mask.preset.save.error.duplicated'
                    defaultMessage='This mask name is already in use' />
                  : defaultErrorBody
                )
              }
            })
          })
          .catch((err) => {
            console.log(err)
            this.setState({
              message: {
                title: errorTitle,
                body: defaultErrorBody
              }
            })
          })
      })
  }

  onDelete (mask) {
    return deleteData(getMasksAPIPath({id: mask.id}))
      .then(this.props.reload)
      .catch(error => {
        console.log(error.message)
        this.setState({
          message: {
            title: mask.name,
            body: <FormattedMessage
              id='survey.mask.preset.delete.error.unknown'
              defaultMessage='There was an error deleting this mask' />
          }
        })
      })
  }

  renderMessage () {
    if (!this.state.message) {
      return ''
    }

    return (
      <div className='modal show'>
        <div className='modal-dialog modal-md'>
          <div className='modal-content'>
            <div className='modal-header'>
              <h5 className='modal-title'>{ this.state.message.title }</h5>
            </div>
            <div className='modal-body'>
              { this.state.message.body }
            </div>
            <div className='modal-footer'>
              <button
                type='button'
                className='btn btn-secondary'
                onClick={() => this.setState({ message: null })}>
                <FormattedMessage
                  id='survey.mask.preset.button.close'
                  defaultMessage='Close' />
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }
}

// Include this to enable `this.props.intl` for this component.
export default injectIntl(SurveyMasks)
