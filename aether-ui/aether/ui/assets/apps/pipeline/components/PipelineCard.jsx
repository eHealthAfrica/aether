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

import PipelineInfoButton from './PipelineInfoButton'
import ContractAddButton from './ContractAddButton'
import ContractCard from './ContractCard'

import { selectPipeline } from '../redux'

class PipelineCard extends Component {
  onPipelineSelect (pipeline) {
    this.props.selectPipeline(pipeline.id)
    this.props.history.push(`/${pipeline.id}`)
  }

  render () {
    const { pipeline } = this.props

    return (
      <div className='pipeline-preview'>
        <div
          className={`preview-input ${pipeline.isInputReadOnly ? 'pipeline-readonly' : ''}`}
          onClick={this.onPipelineSelect.bind(this, pipeline)}>
          { pipeline.isInputReadOnly &&
            <span className='tag'>
              <FormattedMessage
                id='pipeline.card.read-only'
                defaultMessage='read-only'
              />
            </span>
          }

          <div className='input-heading'>
            <span className='badge badge-c badge-big'>
              <i className='fas fa-file fa-sm' />
            </span>
            <span className='input-name'>
              { pipeline.name } { pipeline.mappingset && <PipelineInfoButton pipeline={pipeline} /> }
            </span>
          </div>
        </div>

        <div className='preview-contracts'>
          {
            pipeline.contracts.map(contract => (
              <ContractCard
                key={contract.id}
                contract={contract}
                history={this.props.history}
              />
            ))
          }

          <ContractAddButton pipeline={pipeline} history={this.props.history} />
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({})
const mapDispatchToProps = { selectPipeline }

export default connect(mapStateToProps, mapDispatchToProps)(PipelineCard)
