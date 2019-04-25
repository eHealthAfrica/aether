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

import { ModalError, NavBar, Modal } from '../components'

import PipelineNew from './components/PipelineNew'
import PipelineCard from './components/PipelineCard'

import { getPipelines } from './redux'

class PipelineList extends Component {
  constructor (props) {
    super(props)

    // fetch pipelines list
    props.getPipelines()

    this.state = {
      showDeleteModal: false,
      selectedPipeline: null,
      deleteOptions: {
        entityTpes: true,
        schemaDecorations: true,
        entities: true,
        submissions: true
      }
    }
  }

  onRename (pipeline) {
    console.log(`Rename Pipeline ${pipeline.name}`)
  }

  onDelete (pipeline) {
    this.setState({ showDeleteModal: true, selectedPipeline: pipeline })
  }

  deletePipeline () {
    console.log(`Delete Pipeline ${this.state.selectedPipeline.name}`)
  }

  renderDeletionModal () {
    if (!this.state.showDeleteModal) {
      return null
    }

    const header = (
      <span>
        <FormattedMessage
          id='pipelineList.delete.modal.header'
          defaultMessage='Delete pipeline: '
        />
        <span>{this.state.selectedPipeline.name}</span>
      </span>
    )

    const buttons = (
      <div>
        <button
          data-qa='pipelineList.delete.modal.cancel'
          className='btn btn-w'
          onClick={() => { this.setState({ showDeleteModal: false }) }}>
          <FormattedMessage
            id='pipelineList.delete.modal.cancel.message'
            defaultMessage='Cancel'
          />
        </button>

        <button className='btn btn-w btn-primary' onClick={this.deletePipeline.bind(this)}>
          <FormattedMessage
            id='pipelineList.delete.modal.delete.message'
            defaultMessage='Delete'
          />
        </button>
      </div>
    )

    return (
      <Modal header={header} buttons={buttons}>
        <label className='title-medium'>
          <FormattedMessage
            id='pipelineList.delete.modal.message-1'
            defaultMessage='Deleting this pipeline will also delete:'
          />
        </label>
        <div style={{ marginLeft: '40px' }}>
          <input type='checkbox' checked readOnly />
          <label>
            <FormattedMessage
              id='pipelineList.delete.modal.all.contracts'
              defaultMessage='all Contracts in this pipeline'
            />
          </label>
        </div>
        <label className='title-medium'>
          <FormattedMessage
            id='pipelineList.delete.modal.message-2'
            defaultMessage='Optionally delete:'
          />
        </label>
        <div style={{ marginLeft: '40px' }}>
          <input type='checkbox' checked={this.state.deleteOptions.entityTpes}
            onChange={(e) => {
              this.setState({
                deleteOptions: { ...this.state.deleteOptions, entityTpes: e.target.checked }
              })
            }}
          />
          <label>
            <FormattedMessage
              id='pipelineList.delete.modal.all.entity-types'
              defaultMessage='all Entity Types linked to the pipeline (Schemas)'
            />
          </label>
          <br />
          <input type='checkbox' checked={this.state.deleteOptions.schemaDecorations}
            onChange={(e) => {
              this.setState({
                deleteOptions: { ...this.state.deleteOptions, schemaDecorations: e.target.checked }
              })
            }}
          />
          <label>
            <FormattedMessage
              id='pipelineList.delete.modal.all.schema-decorations'
              defaultMessage='all Schema Decorations used in this pipeline'
            />
          </label>
          <br />
          <input type='checkbox' checked={this.state.deleteOptions.entities}
            onChange={(e) => {
              this.setState({
                deleteOptions: { ...this.state.deleteOptions, entities: e.target.checked }
              })
            }}
          />
          <label>
            <FormattedMessage
              id='pipelineList.delete.modal.all.data'
              defaultMessage='all Data Generated by this pipeline (Entities)'
            />
          </label>
          <br />
          <input type='checkbox' checked={this.state.deleteOptions.submissions}
            onChange={(e) => {
              this.setState({
                deleteOptions: { ...this.state.deleteOptions, submissions: e.target.checked }
              })
            }}
          />
          <label>
            <FormattedMessage
              id='pipelineList.delete.modal.all.submitted'
              defaultMessage='all Submissions made to this pipeline (Submissions)'
            />
          </label>
        </div>
      </Modal>
    )
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
                rename={this.onRename.bind(this, pipeline)}
                delete={this.onDelete.bind(this, pipeline)}
              />
            )) }
          </div>
        </div>
        { this.renderDeletionModal() }
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
