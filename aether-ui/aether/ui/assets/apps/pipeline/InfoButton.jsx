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
import Modal from '../components/Modal'
import { generateGUID } from '../utils'

class InfoButton extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showInfo: false
    }
  }

  setInfoModal (visible, event) {
    event.stopPropagation()
    this.setState({
      showInfo: visible
    })
  }

  render () {
    const { mappingset } = this.props.pipeline
    const submissionUrl = mappingset &&
    `${this.props.kernelUrl}/submissions/?mappingset=${mappingset}`
    const sampleData = {
      mappingset: mappingset,
      revision: generateGUID(),
      payload: this.props.pipeline.input || {}
    }
    return (
      <span>
        <Modal show={this.state.showInfo} header={this.props.pipeline.name}
          buttons={<button type='button' className='btn btn-w btn-primary' onClick={this.setInfoModal.bind(this, false)}>
            <FormattedMessage
              id='info.modal.ok'
              defaultMessage='Ok'
            />
          </button>}>
          {
            submissionUrl
              ? (
                <div>
                  <div className='modal-section'>
                    <label className='form-label'>
                      <FormattedMessage
                        id='info.modal.SubmissionUrl'
                        defaultMessage='Submission URL'
                      />
                    </label>
                    <a href={submissionUrl}>{submissionUrl}</a>
                  </div>
                  <div className='modal-section mt-5'>
                    <label className='form-label'>
                      <FormattedMessage
                        id='info.modal.SubmissionSample'
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
              ) : (
                <span>
                  <FormattedMessage
                    id='info.modal.NotPublished'
                    defaultMessage='Pipeline is not published yet'
                  />
                </span>
              )
          }
        </Modal>
        <i className='fas fa-info-circle published-info-icon' onClick={this.setInfoModal.bind(this, true)} />
      </span>
    )
  }
}

const mapStateToProps = ({ constants }) => ({
  kernelUrl: constants.kernelUrl
})

export default connect(mapStateToProps, {})(InfoButton)
