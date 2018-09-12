/*
 * Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import React, { Component } from 'react'
import { connect } from 'react-redux'
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'

const MESSAGES = defineMessages({
  placeholder: {
    defaultMessage: 'Name of new pipeline',
    id: 'pipeline.new.name.placeholder'
  }
})

class NewPipeline extends Component {
  constructor (props) {
    super(props)

    this.state = {
      view: 'button',
      newPipelineName: ''
    }
  }

  render () {
    return (
      <div className='pipeline-new'>
        { this.state.view === 'button' ? this.renderButton() : this.renderForm() }
      </div>
    )
  }

  renderButton () {
    return (
      <button
        type='button'
        className='btn btn-c btn-big'
        onClick={() => this.setState({ view: 'form' })}>
        <span className='details-title'>
          <FormattedMessage
            id='pipeline.new.button.new'
            defaultMessage='New pipeline'
          />
        </span>
      </button>
    )
  }

  renderForm () {
    const { formatMessage } = this.props.intl
    const onSubmit = (event) => {
      event.preventDefault()

      this.props.onStartPipeline({ name: this.state.newPipelineName })
    }

    return (
      <form className='pipeline-form' onSubmit={onSubmit}>
        <div className='form-group'>
          <input
            type='text'
            required
            name='name'
            className='text-input'
            placeholder={formatMessage(MESSAGES.placeholder)}
            value={this.state.newPipelineName}
            onChange={event => this.setState({ newPipelineName: event.target.value })}
          />
          <label className='form-label'>
            <FormattedMessage
              id='pipeline.new.name'
              defaultMessage='Name of new pipeline'
            />
          </label>
        </div>
        <button
          type='button'
          className='btn btn-c btn-big btn-transparent'
          onClick={() => this.setState({ view: 'button', newPipelineName: '' })}>
          <span className='details-title'>
            <FormattedMessage
              id='pipeline.new.button.cancel'
              defaultMessage='Cancel'
            />
          </span>
        </button>
        <button
          type='submit'
          className='btn btn-c btn-big'>
          <span className='details-title'>
            <FormattedMessage
              id='pipeline.new.button.ok'
              defaultMessage='Start pipeline'
            />
          </span>
        </button>
      </form>
    )
  }
}

export default connect()(injectIntl(NewPipeline))
