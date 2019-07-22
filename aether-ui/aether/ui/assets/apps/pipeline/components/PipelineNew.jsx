/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

import { addPipeline } from '../redux'

const MESSAGES = defineMessages({
  namePlaceholder: {
    defaultMessage: 'Name of new pipeline',
    id: 'pipeline.new.name.placeholder'
  }
})

class PipelineNew extends Component {
  constructor (props) {
    super(props)

    this.state = {
      view: 'button',
      pipelineName: '',
      submitted: false
    }
  }

  componentDidUpdate (prevProps) {
    if (this.state.submitted) {
      if (this.props.pipeline && prevProps.pipeline !== this.props.pipeline) {
        this.props.history.push(`/${this.props.pipeline.id}`)
      }
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
        className='btn btn-c btn-big new-input'
        onClick={() => { this.setState({ view: 'form' }) }}>
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
      event.stopPropagation()

      this.setState({
        submitted: true
      }, () => this.props.addPipeline({ name: this.state.pipelineName }))
    }

    return (
      <form className='pipeline-form' onSubmit={onSubmit}>
        <div className='form-group'>
          <input
            type='text'
            required
            name='name'
            className='text-input'
            placeholder={formatMessage(MESSAGES.namePlaceholder)}
            value={this.state.pipelineName}
            onChange={event => { this.setState({ pipelineName: event.target.value }) }}
          />
          <label className='form-label'>
            { formatMessage(MESSAGES.namePlaceholder) }
          </label>
        </div>

        <button
          type='button'
          className='btn btn-c btn-big btn-transparent'
          onClick={() => { this.setState({ view: 'button', pipelineName: '' }) }}>
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

const mapStateToProps = ({ pipelines }) => ({
  pipeline: pipelines.currentPipeline
})
const mapDispatchToProps = { addPipeline }

export default connect(mapStateToProps, mapDispatchToProps)(injectIntl(PipelineNew))
