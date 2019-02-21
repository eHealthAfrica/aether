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
import { FormattedMessage } from 'react-intl'

import Modal from '../../components/Modal'

import { getKernelURL } from '../../redux/settings'

class PipelineInfoButton extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showInfo: false
    }

    props.getKernelURL()
  }

  render () {
    const { pipeline, kernelUrl } = this.props
    const submissionUrl = `${kernelUrl}/submissions/?mappingset=${pipeline.mappingset}`

    const sampleData = {
      mappingset: pipeline.mappingset,
      payload: pipeline.input || {}
    }

    const execute = (event, showInfo) => {
      event.stopPropagation()

      this.setState({ showInfo })
    }

    return (
      <span>
        <i
          className='fas fa-info-circle published-info-icon'
          onClick={(event) => { execute(event, true) }}
        />

        { this.state.showInfo &&
          <Modal
            header={pipeline.name}
            buttons={
              <button
                type='button'
                className='btn btn-w btn-primary'
                onClick={(event) => { execute(event, false) }}>
                <FormattedMessage id='pipeline.info.modal.ok' defaultMessage='OK' />
              </button>
            }>
            <div>
              <div className='modal-section'>
                <label className='form-label'>
                  <FormattedMessage
                    id='pipeline.info.modal.url'
                    defaultMessage='Submission URL'
                  />
                </label>
                <a href={submissionUrl}>{submissionUrl}</a>
              </div>

              <div className='modal-section mt-5'>
                <label className='form-label'>
                  <FormattedMessage
                    id='pipeline.info.modal.sample'
                    defaultMessage='Submission sample data'
                  />
                </label>
                <div className='code'>
                  <code>
                    { JSON.stringify(sampleData || [], 0, 2) }
                  </code>
                </div>
              </div>
            </div>
          </Modal>
        }
      </span>
    )
  }
}

const mapStateToProps = ({ settings }) => ({
  kernelUrl: settings.kernelUrl
})
const mapDispatchToProps = { getKernelURL }

export default connect(mapStateToProps, mapDispatchToProps)(PipelineInfoButton)
