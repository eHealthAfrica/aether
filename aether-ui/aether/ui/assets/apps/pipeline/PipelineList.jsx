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
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { NavBar } from '../components'

import PipelineNew from './components/PipelineNew'
import PipelineCard from './components/PipelineCard'

import { getPipelines } from './redux'

const PipelineList = ({ getPipelines, loading, pipelinesList }) => {
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    if (!initialized) {
      setInitialized(true)
      getPipelines()
    }
  })

  return (
    <div className='pipelines-container show-index'>
      <NavBar />

      <div className='pipelines'>
        <h1 className='pipelines-heading'>
          <FormattedMessage
            id='pipeline.list.pipelines'
            defaultMessage='Pipelines'
          />
          <button
            type='button'
            className='btn btn-c float-end'
            onClick={() => { setInitialized(false) }}
            disabled={loading}
          >
            <i className={`me-2 fas ${loading ? ' fa-recycle' : 'fa-sync'}`} />
            <FormattedMessage
              id='pipeline.list.refresh'
              defaultMessage='Reload'
            />
          </button>
        </h1>

        <PipelineNew />

        <div className='pipeline-previews'>
          {
            (pipelinesList || []).map(pipeline => (
              <PipelineCard key={pipeline.id} pipeline={pipeline} />
            ))
          }
        </div>
      </div>
    </div>
  )
}

const mapStateToProps = ({ pipelines: { loading, pipelinesList } }) => ({ loading, pipelinesList })
const mapDispatchToProps = { getPipelines }

export default connect(mapStateToProps, mapDispatchToProps)(PipelineList)
