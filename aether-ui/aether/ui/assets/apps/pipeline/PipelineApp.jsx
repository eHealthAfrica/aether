/*
 * Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import { hot } from 'react-hot-loader'
import React from 'react'
import { connect } from 'react-redux'
import { Route, Switch } from 'react-router-dom'

import { LoadingSpinner, ModalError } from '../components'

import PipelineList from './PipelineList'
import Pipeline from './Pipeline'

const PipelineApp = ({ loading, error }) => (
  <>
    <Route render={() => (
      <Switch>
        <Route exact path='/' component={PipelineList} />
        <Route path='/:pid/:cid/:view' component={Pipeline} />
        <Route path='/:pid/:cid' component={Pipeline} />
        <Route path='/:pid' component={Pipeline} />
      </Switch>
    )}
    />

    {loading && <LoadingSpinner />}
    {error && <ModalError error={error} />}
  </>
)

const mapStateToProps = ({ pipelines: { loading, error } }) => ({ loading, error })

export default hot(module)(
  connect(mapStateToProps)(PipelineApp)
)
