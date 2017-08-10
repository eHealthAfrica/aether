import React, { Component } from 'react'

import SurveyorForm from './SurveyorForm'

export default class SurveyorsList extends Component {
  constructor (props) {
    super(props)
    this.state = {}
  }

  render () {
    const {surveyors} = this.props
    const {surveyor} = this.state
    const enableActions = (surveyor === undefined)

    return (
      <div className='surveys-list' data-qa='surveyors-list'>
        <div className='surveys-list__header'>
          <h1>eHealth Africa (Org name)</h1>
          <div>
            {
              enableActions &&
              <button className='btn btn-primary btn-icon' onClick={this.add.bind(this)}>
                <i className='fa fa-plus-circle' />
                New surveyor
              </button>
            }
          </div>
        </div>

        <table className='table table-hover'>
          <thead>
            <tr>
              <th className='title'>Surveyors</th>
              <th />
            </tr>
          </thead>

          <tbody>
            {
              surveyors.results.map(surveyor => (
                <tr key={surveyor.id}>
                  <td>{surveyor.username}</td>
                  <td>
                    {
                      enableActions &&
                      <button
                        className='btn btn-primary pull-right'
                        onClick={(evt) => this.edit(evt, surveyor)}
                      ><i className='fa fa-pencil' /></button>
                    }
                  </td>
                </tr>
              ))
            }
          </tbody>
        </table>

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
