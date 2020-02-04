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
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'
import { Modal } from '../../components'

const MESSAGES = defineMessages({
  namePlaceholder: {
    defaultMessage: 'Name of pipeline',
    id: 'rename.modal.name.placeholder'
  }
})

class PipelineRename extends Component {
  constructor (props) {
    super(props)
    this.state = {
      name: props.name || ''
    }
  }

  render () {
    const { formatMessage } = this.props.intl

    const onSubmit = (event) => {
      event.preventDefault()
      event.stopPropagation()
      this.props.onSave(this.state.name)
    }

    const buttons = (
      <div>
        <button
          data-qa='rename.modal.button.cancel'
          className='btn btn-w'
          onClick={this.props.onCancel}
        >
          <FormattedMessage
            id='rename.modal.button.cancel'
            defaultMessage='Cancel'
          />
        </button>

        <button className='btn btn-w btn-primary' onClick={onSubmit}>
          <FormattedMessage
            id='rename.modal.button.save'
            defaultMessage='Save'
          />
        </button>
      </div>
    )

    return (
      <Modal
        onEnter={onSubmit}
        onEscape={this.props.onCancel}
        buttons={buttons}
        header={
          <FormattedMessage
            defaultMessage='Rename pipeline {name}'
            id='rename.modal.header'
            values={{ name: <b>{this.props.name}</b> }}
          />
        }
      >
        <form>
          <div className='form-group'>
            <label className='form-label'>
              <FormattedMessage
                id='rename.modal.name.label'
                defaultMessage='Pipeline name'
              />
            </label>
            <input
              type='text'
              required
              name='name'
              className='text-input input-large'
              placeholder={formatMessage(MESSAGES.namePlaceholder)}
              value={this.state.name}
              onChange={event => { this.setState({ name: event.target.value }) }}
            />
          </div>
        </form>
      </Modal>
    )
  }
}

export default injectIntl(PipelineRename)
