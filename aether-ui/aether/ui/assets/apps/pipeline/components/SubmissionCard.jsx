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

import { getKernelURL } from '../../redux/settings'

class SubmissionCard extends Component {
  constructor (props) {
    super(props)

    props.getKernelURL()
  }

  render () {
    const submissionUrl = `${this.props.kernelUrl}/submissions/`
    const sampleData = {
      mappingset: this.props.mappingset,
      payload: this.props.inputData || {}
    }

    return (
      <div className='mt-4'>
        <label className='form-label'>
          <FormattedMessage
            id='submission.card.url'
            defaultMessage='Submission URL'
          />
        </label>
        <a className='submission-url' href={submissionUrl}>
          { submissionUrl }
        </a>

        <div className='mt-5'>
          <label className='form-label'>
            <FormattedMessage
              id='submission.card.sample'
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
    )
  }
}

const mapStateToProps = ({ settings }) => ({
  kernelUrl: settings.kernelUrl
})
const mapDispatchToProps = { getKernelURL }

export default connect(mapStateToProps, mapDispatchToProps)(SubmissionCard)
