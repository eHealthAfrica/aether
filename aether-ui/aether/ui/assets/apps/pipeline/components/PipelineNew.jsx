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

import React, { useState, useEffect } from 'react'
import { useHistory } from 'react-router-dom'
import { connect } from 'react-redux'
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'

import { addPipeline } from '../redux'

const MESSAGES = defineMessages({
  namePlaceholder: {
    defaultMessage: 'Name of new pipeline',
    id: 'pipeline.new.name.placeholder'
  }
})

const PipelineNew = ({ pipeline, addPipeline, intl: { formatMessage } }) => {
  const history = useHistory()
  const [view, setView] = useState('button')
  const [name, setName] = useState('')
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    if (submitted && pipeline) {
      history.push(`/${pipeline.id}`)
    }
  })

  const onSubmit = (event) => {
    event.preventDefault()
    event.stopPropagation()

    setSubmitted(true)
    addPipeline({ name })
  }

  return (
    <div className='pipeline-new'>
      {
        view === 'button'
          ? (
            <button
              type='button'
              className='btn btn-c btn-big new-input'
              onClick={() => { setView('form') }}
            >
              <span className='details-title'>
                <FormattedMessage
                  id='pipeline.new.button.new'
                  defaultMessage='New pipeline'
                />
              </span>
            </button>
          )
          : (
            <form className='pipeline-form' onSubmit={onSubmit}>
              <div className='form-group'>
                <input
                  type='text'
                  required
                  name='name'
                  className='text-input'
                  placeholder={formatMessage(MESSAGES.namePlaceholder)}
                  value={name}
                  onChange={event => { setName(event.target.value) }}
                />
                <label className='form-label'>
                  {formatMessage(MESSAGES.namePlaceholder)}
                </label>
              </div>

              <button
                type='button'
                className='btn btn-c btn-big btn-transparent'
                onClick={() => {
                  setView('button')
                  setName('')
                }}
              >
                <span className='details-title'>
                  <FormattedMessage
                    id='pipeline.new.button.cancel'
                    defaultMessage='Cancel'
                  />
                </span>
              </button>

              <button type='submit' className='btn btn-c btn-big'>
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
    </div>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  pipeline: pipelines.currentPipeline
})
const mapDispatchToProps = { addPipeline }

export default connect(mapStateToProps, mapDispatchToProps)(injectIntl(PipelineNew))
