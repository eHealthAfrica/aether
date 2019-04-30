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
        entityTypes: false,
        entities: false,
        submissions: false
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
          id='pipeline.delete.modal.header'
          defaultMessage='Delete pipeline '
        />
        <span className='bold'>{this.state.selectedPipeline.name}?</span>
      </span>
    )

    const buttons = (
      <div>
        <button
          data-qa='pipelineList.delete.cancel'
          className='btn btn-w'
          onClick={() => { this.setState({ showDeleteModal: false }) }}>
          <FormattedMessage
            id='pipelineList.delete.cancel'
            defaultMessage='Cancel'
          />
        </button>

        <button className='btn btn-w btn-primary' onClick={this.deletePipeline}>
          <FormattedMessage
            id='pipelineList.delete.button'
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
            defaultMessage='This will also delete:'
          />
        </label>
        <div className='check-readonly ml-4'>
          <input type='checkbox' checked readOnly />
          <label>
            <FormattedMessage
              id='pipelineList.delete.modal.all.contracts'
              defaultMessage='Contracts contained in this pipeline'
            />
          </label>
        </div>
        <label className='title-medium mt-4'>
          <FormattedMessage
            id='pipelineList.delete.modal.message-2'
            defaultMessage='Would you also like to delete any of the following?'
          />
        </label>
        <div className='check-default ml-4'>
          <input type='checkbox' id='check1' checked={this.state.deleteOptions.submissions}
            onChange={(e) => {
              this.setState({
                deleteOptions: { ...this.state.deleteOptions, submissions: e.target.checked }
              })
            }}
          />
          <label for='check1'>
            <FormattedMessage
              id='pipelineList.delete.modal.all.submissions-0'
              defaultMessage='Data'
            />
            <span style={{ fontWeight: 'bold' }}>
              <FormattedMessage
                id='pipelineList.delete.modal.all.submissions-1'
                defaultMessage='&nbsp;submitted to&nbsp;'
              />
            </span>
            <FormattedMessage
              id='pipelineList.delete.modal.all.submissions-2'
              defaultMessage='this pipeline (Submissions)'
            />
          </label>
        </div>
        <div className='check-default ml-4'>
          <input type='checkbox' id='check2' checked={this.state.deleteOptions.entityTypes}
            onChange={(e) => {
              this.setState({
                deleteOptions: {
                  ...this.state.deleteOptions,
                  entityTypes: e.target.checked,
                  entities: e.target.checked
                }
              })
            }}
          />
          <label for='check2'>
            <FormattedMessage
              id='pipelineList.delete.modal.all.entity-types-0'
              defaultMessage='Entity Types (Schemas)'
            />
          </label>
        </div>
        <div className='check-default ml-4' style={{ paddingLeft: '40px' }}>
          <input type='checkbox' id='check3' checked={this.state.deleteOptions.entities}
            onChange={(e) => {
              if (!e.target.checked) {
                this.setState({
                  deleteOptions: {
                    ...this.state.deleteOptions,
                    entities: e.target.checked,
                    entityTypes: e.target.checked
                  }
                })
              } else {
                this.setState({
                  deleteOptions: { ...this.state.deleteOptions, entities: e.target.checked }
                })
              }
            }}
          />
          <label for='check3'>
            <FormattedMessage
              id='pipelineList.delete.modal.all.data-0'
              defaultMessage='Data'
            />
            <span style={{ fontWeight: 'bold' }}>
              <FormattedMessage
                id='pipelineList.delete.modal.all.data-1'
                defaultMessage='&nbsp;created by&nbsp;'
              />
            </span>
            <FormattedMessage
              id='pipelineList.delete.modal.all.data-2'
              defaultMessage='this pipeline (Entities)'
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
