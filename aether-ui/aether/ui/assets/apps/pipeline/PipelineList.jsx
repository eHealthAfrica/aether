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

import { ModalError, NavBar } from '../components'

import PipelineNew from './components/PipelineNew'
import PipelineCard from './components/PipelineCard'

import { getPipelines } from './redux'

class PipelineList extends Component {
  constructor (props) {
    super(props)

    // fetch pipelines list
    props.getPipelines()
  }

  render () {
    return (
      <div className='pipelines-container show-index'>
        { this.props.error && <ModalError error={this.props.error} /> }
        <NavBar />

        <div className='pipelines'>
          <h1 className='pipelines-heading'>
            <FormattedMessage
              id='pipeline.list.pipelines'
              defaultMessage='Pipelines'
            />
          </h1>

          <PipelineNew history={this.props.history} />

          <div className='pipeline-previews'>
            { this.props.list.map(pipeline => (
              <PipelineCard
                key={pipeline.id}
                pipeline={pipeline}
                history={this.props.history}
              />
            )) }
          </div>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  list: pipelines.pipelineList || [],
  error: pipelines.error
})
const mapDispatchToProps = { getPipelines }

export default connect(mapStateToProps, mapDispatchToProps)(PipelineList)
