import React, { Component } from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { PROJECT_NAME } from '../utils/constants'
import { NavBar, PaginationContainer } from '../components'

import NewPipeline from './NewPipeline'
import { pipelineActions } from './redux'
import { PIPELINES_URL } from './api'

class PipelineList extends Component {
  constructor (props) {
    super(props)
    this.state = {
      view: 'show-index'
    }
  }

  componentWillReceiveProps (nextProps) {
    pipelineActions.setPipelines(nextProps.list)
  }

  render () {
    return (
      <div className={`pipelines-container ${this.state.view}`}>
        <NavBar />

        <div className='pipelines'>
          <h1 className='pipelines-heading'>
            { PROJECT_NAME }
            <span> // </span>
            <FormattedMessage
              id='pipeline.list.pipelines'
              defaultMessage='Pipelines'
            />
          </h1>

          <NewPipeline onAdd={pipeline => { this.onStartNewPipeline(pipeline) }} />

          <div className='pipeline-previews'>
            { this.renderPipelineCards() }
          </div>
        </div>
      </div>
    )
  }

  renderPipelineCards () {
    return this.props.list.map(pipeline => (
      <div
        key={pipeline.id}
        className='pipeline-preview'
        onClick={() => { this.onSelectPipeline(pipeline) }}>
        <h2 className='preview-heading'>{pipeline.name}</h2>

        <div className='summary-entity-types'>
          <span className='badge badge-b badge-big'>{pipeline.entityTypes}</span>
          <FormattedMessage
            id='pipeline.list.entity.types'
            defaultMessage='Entity-Types'
          />
        </div>

        <div className='summary-errors'>
          <span className='badge badge-b badge-big'>{pipeline.errors}</span>
          <FormattedMessage
            id='pipeline.list.errors'
            defaultMessage='Errors'
          />
        </div>
      </div>
    ))
  }

  onStartNewPipeline (newPipeline) {
    this.props.dispatch(pipelineActions.addPipeline(newPipeline))
    this.onSelectPipeline(newPipeline)
  }

  onSelectPipeline (pipeline) {
    this.props.dispatch(pipelineActions.selectedPipelineChanged(pipeline))
    this.props.history.push(`/${pipeline.id}`)
  }
}

class PipelineListContainer extends Component {
  render () {
    return (
      <PaginationContainer
        extras={this.props}
        url={PIPELINES_URL}
        listComponent={PipelineList}
        pageSize={100}
      />
    )
  }
}

export default connect()(PipelineListContainer)
