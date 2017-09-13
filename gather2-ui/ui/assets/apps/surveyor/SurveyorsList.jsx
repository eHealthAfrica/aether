import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

import { ORG_NAME } from '../utils/env'
import SurveyorForm from './SurveyorForm'

export default class SurveyorsList extends Component {
  constructor (props) {
    super(props)
    this.state = {}
  }

  render () {
    const {list} = this.props
    const {surveyor} = this.state
    const enableActions = (surveyor === undefined)

    return (
      <div data-qa='surveyors-list' className='page-container'>
        <div className='page-header'>
          <h1 data-qa='organization-name'>{ ORG_NAME }</h1>
          <div>
            {
              enableActions &&
              <button className='btn btn-primary btn-icon' onClick={this.add.bind(this)}>
                <i className='fa fa-plus-circle mr-3' />
                <FormattedMessage
                  id='surveyor.list.action.add'
                  defaultMessage='New surveyor' />
              </button>
            }
          </div>
        </div>

        {
          list.length > 0 &&
          <div className='page-content'>
            <h4 className='title'>
              <FormattedMessage
                id='surveyor.list.title'
                defaultMessage='Surveyors' />
            </h4>

            <div className='surveyors'>
              {
                list.map((surveyor) => (
                  <div key={surveyor.id} className='surveyor-list-item'>
                    <div className='surveyor-header'>
                      <i className='fa fa-user mr-2' />
                      {surveyor.username}

                      {
                        enableActions &&
                        <button
                          className='btn btn-sm btn-secondary pull-right'
                          onClick={(evt) => this.edit(evt, surveyor)}
                        ><i className='fa fa-pencil' /></button>
                      }
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        }

        {
          surveyor &&
          <div className='form-overlay'>
            <SurveyorForm
              surveyor={this.state.surveyor}
              onCancel={this.cancel.bind(this)} />
          </div>
        }

      </div>
    )
  }

  cancel (event) {
    event.preventDefault()
    this.setState({ surveyor: undefined })
  }

  add (event) {
    event.preventDefault()
    this.setState({ surveyor: {} })
  }

  edit (event, surveyor) {
    event.preventDefault()
    this.setState({ surveyor })
  }
}
