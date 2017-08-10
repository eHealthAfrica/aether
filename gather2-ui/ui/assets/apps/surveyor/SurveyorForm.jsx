import React, { Component } from 'react'

import { clone } from '../utils'
import { deleteData, postData, putData } from '../utils/request'

export default class SurveyorForm extends Component {
  constructor (props) {
    super(props)
    this.state = { ...clone(this.props.surveyor), errors: {} }
  }

  render () {
    const surveyor = this.state
    const isNew = (surveyor.id === undefined)
    const title = (isNew ? 'New surveyor' : `Edit surveyor: ${this.props.surveyor.username}`)

    return (
      <div className='surveyor-edit' data-qa='edit-surveyor'>
        <h3>{title}</h3>

        { this.renderErrors(surveyor.errors.global) }

        <form onSubmit={this.onSubmit.bind(this)}>
          <div className='form-group big-input'>
            <label className='form-control-label title'>Surveyor username</label>
            <input
              name='username'
              type='text'
              className='form-control'
              required
              value={surveyor.username || ''}
              onChange={this.onInputChange.bind(this)}
            />
            { this.renderErrors(surveyor.errors.username) }
          </div>

          <div className='form-group big-input'>
            <label className='form-control-label title'>Password</label>
            <input
              name='password_1'
              type='password'
              className='form-control'
              required={isNew}
              value={surveyor.password_1 || ''}
              onChange={this.onInputChange.bind(this)}
            />
            { this.renderErrors(surveyor.errors.password) }
            {
              this.renderWarnings([
                'The password must contain at least 10 characters.',
                'The password can\'t be too similar to your other personal information.',
                'The password can\'t be a commonly used password.',
                'The password can\'t be entirely numeric.'
              ])
            }
          </div>

          <div className='form-group big-input'>
            <label className='form-control-label title'>Repeat password</label>
            <input
              name='password_2'
              type='password'
              className='form-control'
              required={isNew || surveyor.password_1}
              value={surveyor.password_2 || ''}
              onChange={this.onInputChange.bind(this)}
            />
          </div>

          <div className='row actions'>
            <div className='col-sm-6'>
              { !isNew &&
                <button
                  type='button'
                  className='btn btn-delete pull-right col-sm-6'
                  onClick={this.onDelete.bind(this)}>
                  Delete Surveyor
                </button>
              }
            </div>
            <div className='col-sm-3'>
              <button
                type='button'
                className='btn btn-cancel btn-block'
                onClick={(evt) => this.props.onCancel(evt)}>
                Cancel
              </button>
            </div>
            <div className='col-sm-3'>
              <button type='submit' className='btn btn-primary btn-block'>
                Save Surveyor
              </button>
            </div>
          </div>
        </form>
      </div>
    )
  }

  renderErrors (errors) {
    if (!errors || !errors.length) {
      return ''
    }

    return (
      <div data-qa='data-erred'>
        {
          errors.map((error, index) => (
            <p className='badge badge-danger' key={index}>
              <i className='fa fa-warning' />
              &nbsp;
              { error }
            </p>
          ))
        }
      </div>
    )
  }

  renderWarnings (warnings) {
    if (!warnings || !warnings.length) {
      return ''
    }

    return (
      <div data-qa='data-warning'>
        {
          warnings.map((warning, index) => (
            <div key={index}>
              <small className='badge badge-warning'>
                { warning }
              </small>
            </div>
          ))
        }
      </div>
    )
  }

  onInputChange (event) {
    event.preventDefault()
    this.setState({ [event.target.name]: event.target.value })
  }

  validatePassword () {
    if (!this.state.id || this.state.password_1) {
      // validate password
      if (this.state.password_1 !== this.state.password_2) {
        this.setState({
          errors: {
            password: ['The two password fields didn\'t match.']
          }
        })
        return false
      }

      if (this.state.password_1.length < 10) {
        this.setState({
          errors: {
            password: ['This password is too short. It must contain at least 10 characters.']
          }
        })
        return false
      }
    }

    return true
  }

  onSubmit (event) {
    event.preventDefault()

    if (!this.validatePassword()) {
      return
    }

    const surveyor = {
      username: this.state.username,
      password: this.state.password_1 || this.props.surveyor.password
    }

    const saveMethod = (this.state.id ? putData : postData)
    const url = '/odk/surveyors' + (this.state.id ? '/' + this.state.id : '') + '.json'

    return saveMethod(url, surveyor)
      .then(response => {
        // navigate to Surveyors list page
        window.location.pathname = '/surveyors'
      })
      .catch(error => {
        try {
          return error.response.json()
        } catch (e) {
          console.log('error', e)
          this.setState({
            errors: {
              global: [`An error occurred while saving “${surveyor.username}”`]
            }
          })
        }
      })
      .then(response => {
        if (!response) return
        this.setState({ errors: response })
      })
  }

  onDelete (event) {
    event.preventDefault()

    const surveyor = this.state

    // check if there were changes
    const shouldDelete = window.confirm(
      `Are you sure you want to delete the surveyor “${surveyor.username}”?`)

    if (shouldDelete) {
      return deleteData(`/odk/surveyors/${surveyor.id}.json`)
        .then(() => {
          // navigate to Surveyors list page
          window.location.pathname = '/surveyors'
        })
        .catch(error => {
          console.log(error.message)
          this.setState({
            errors: {
              global: [`An error occurred while deleting “${surveyor.username}”`]
            }
          })
        })
    }
  }
}
