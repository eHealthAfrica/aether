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
import { FormattedMessage } from 'react-intl'

import Modal from './Modal'

export default class ModalError extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showError: props.error && props.error.message
    }
  }

  componentDidUpdate (prevProps) {
    if (prevProps.error !== this.props.error) {
      this.setState({
        showError: this.props.error && this.props.error.message
      })
    }
  }

  render () {
    if (!this.state.showError) {
      return ''
    }

    const close = (event) => {
      event.stopPropagation()
      this.setState({ showError: false })
    }

    return (
      <Modal
        onEnter={close}
        onEscape={close}
        header={
          <>
            <FormattedMessage
              id='modal.error.header'
              defaultMessage='Error code'
            /> {this.props.error.status}
          </>
        }
        buttons={
          <button
            type='button'
            className='btn btn-w btn-primary'
            onClick={close}
          >
            <FormattedMessage id='modal.error.ok' defaultMessage='OK' />
          </button>
        }
      >
        {this.props.error.message}
      </Modal>
    )
  }
}
