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
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'

class Output extends Component {
  render () {
    return (
      <div className='section-body'>
        <div className='pipeline-data pipeline-errors'>
          <h3 className='title-medium'>
            <FormattedMessage id='output.mapping_errors' defaultMessage='Mapping errors' />
          </h3>
          <ul>
            { this.props.selectedPipeline.mapping_errors && this.props.selectedPipeline.mapping_errors.map((error, index) => (
              <li key={`${error.path}_${index}`}>
                <span className='error-description'>{error.description}</span>
                <span className='error-path'>{error.path ? `"${error.path}"` : ''}</span>
              </li>
            )) }
          </ul>
        </div>
        <div className='pipeline-data'>
          <h3 className='title-medium'>
            <FormattedMessage id='output.data' defaultMessage='Output.data' />
          </h3>
          <code>
            { JSON.stringify(this.props.selectedPipeline.output || [], 0, 2) }
          </code>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps)(Output)
