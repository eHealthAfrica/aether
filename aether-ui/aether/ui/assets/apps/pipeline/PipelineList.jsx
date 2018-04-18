import React, { Component } from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { PROJECT_NAME } from '../utils/constants'
import { NavBar } from '../components'

import NewPipeline from './NewPipeline'
import { addPipeline, selectedPipelineChanged, getPipelines } from './redux'

class PipelineList extends Component {
  constructor (props) {
    super(props)
    this.state = {
      view: 'show-index'
    }
  }

  componentWillMount () {
    this.props.getPipelines()
  }

  componentWillReceiveProps (nextProps) {
    if (nextProps.error !== this.props.error) {
      // TODO: handle errors
    }
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

          <NewPipeline
            onStartPipeline={newPipeline => { this.onStartPipeline(newPipeline) }}
          />

          <div className='pipeline-previews'>
            { this.renderPipelineCards() }
          </div>
        </div>
      </div>
    )
  }

  renderPipelineCards () {
    return this.props.pipelineList.map(pipeline => (
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

  onStartPipeline (newPipeline) {
    this.props.addPipeline(newPipeline)
    this.onSelectPipeline(newPipeline)
  }

  onSelectPipeline (pipeline) {
    this.props.selectedPipelineChanged(pipeline)
    this.props.history.push('/pipeline')
  }
}

const mapStateToProps = ({ pipelines }) => ({
  pipelineList: pipelines.pipelineList,
  error: pipelines.error
})

export default connect(mapStateToProps, { getPipelines, selectedPipelineChanged, addPipeline })(PipelineList)
