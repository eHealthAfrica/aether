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
import { FormattedMessage } from 'react-intl'

import Modal from '../../components/Modal'
import SubmissionCard from './SubmissionCard'

class PipelineInfoButton extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showInfo: false
    }
  }

  render () {
    const { pipeline } = this.props

    const execute = (event, showInfo) => {
      event.stopPropagation()
      this.setState({ showInfo })
    }
    const hide = (event) => { execute(event, false) }

    return (
      <>
        <i
          className='ml-1 fas fa-info-circle published-info-icon'
          onClick={(event) => { execute(event, true) }}
        />

        {
          this.state.showInfo &&
            <Modal
              header={pipeline.name}
              buttons={
                <button
                  type='button'
                  className='btn btn-w btn-primary'
                  onClick={hide}
                >
                  <FormattedMessage id='pipeline.info.modal.ok' defaultMessage='OK' />
                </button>
              }
            >
              <div>
                <SubmissionCard
                  mappingset={pipeline.mappingset}
                  inputData={pipeline.input}
                />
              </div>
            </Modal>
        }
      </>
    )
  }
}

export default connect()(PipelineInfoButton)
