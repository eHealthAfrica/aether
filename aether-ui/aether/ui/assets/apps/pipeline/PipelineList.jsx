import React, { Component } from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'
import moment from 'moment'

import { PROJECT_NAME } from '../utils/constants'
import { NavBar, PublishButton } from '../components'

import NewPipeline from './NewPipeline'
import { addPipeline, selectedPipelineChanged, getPipelines, fetchPipelines } from './redux'

class PipelineList extends Component {
  constructor (props) {
    super(props)
    this.state = {
      view: 'show-index'
    }
  }

  componentWillMount () {
    if (!this.props.pipelineList.length) {
      this.props.getPipelines()
    }
    this.props.fetchPipelines()
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
        className='pipeline-preview'>
        <div
          onClick={() => { this.onSelectPipeline(pipeline) }}>
          <h2 className='preview-heading'>{pipeline.name}</h2>

          <div className='summary-entity-types'>
            <span className='badge badge-b badge-big'>
              { pipeline.entity_types ? pipeline.entity_types.length : 0 }
            </span>
            <FormattedMessage
              id='pipeline.list.entity.types'
              defaultMessage='Entity-Types'
            />
          </div>

          <div className='summary-errors'>
            <span className='badge badge-b badge-big'>
              { pipeline.mapping_errors ? pipeline.mapping_errors.length : 0 }
            </span>
            <FormattedMessage
              id='pipeline.list.errors'
              defaultMessage='Errors'
            />
          </div>
        </div>
        <div className='pipeline-publish'>
          <div className='status-publish'>
            <FormattedMessage
              id='pipeline.list.publish-status'
              defaultMessage={pipeline.published_on ? `Published on ${moment(new Date(pipeline.published_on)).format('MMMM DD')}`
                : 'Not published'}
            />
          </div>
          <PublishButton pipeline={pipeline} className='btn btn-w btn-publish' />
        </div>

      </div>
    ))
  }

  onStartPipeline (newPipeline) {
    this.props.addPipeline(newPipeline)
    this.props.history.push(`/${newPipeline.id}`)
  }

  onSelectPipeline (pipeline) {
    this.props.selectedPipelineChanged(pipeline)
    this.props.history.push(`/${pipeline.id}`)
  }
}

const mapStateToProps = ({ pipelines }) => ({
  pipelineList: pipelines.pipelineList,
  error: pipelines.error
})

export default connect(mapStateToProps, { getPipelines, selectedPipelineChanged, addPipeline, fetchPipelines })(PipelineList)
