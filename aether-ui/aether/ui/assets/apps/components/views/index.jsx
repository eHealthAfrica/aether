import React, { Component } from 'react'
import { connect } from 'react-redux'
import { PROJECT_NAME } from '../../utils/constants'
import NewPipeLine from './pipelines/new_pipeline'
import { selectedPipelineChanged } from '../../redux/modules/pipeline'
import PipelineCard from './pipelines/cards'

class Home extends Component {
  constructor (props) {
    super(props)
    this.state = {
      view: 'show-index'
    }
  }

  startPipeline (selectedPipeline) {
    this.props.selectedPipelineChanged(selectedPipeline)
    this.props.history.push('/pipeline')
  }

  getPipelineCards () {
    const cards = []
    this.props.pipelineList.forEach(pipeline => {
      if (pipeline) {
        cards.push(
          <PipelineCard
            pipeline={pipeline}
            onSelect={() => {
              this.props.selectedPipelineChanged(pipeline)
              this.props.history.push('/pipeline')
            }}
            key={pipeline.id}
          />
        )
      }
    })
    return cards
  }

  render () {
    return (
      <div className={`pipelines-container ${this.state.view}`}>
        <div className='navbar top-nav'>
          <a className='top-nav-logo' href='/' title='aether'>
            <div className='logo-container'>
              <div className='flipper'>
                <div className='front' />
                <div className='back' />
              </div>
            </div>
            <span data-app-name='app-name'><b>ae</b>ther</span>
          </a>
          <div className='top-nav-user'>
            <span
              id='logged-in-user-info'>
              User name
            </span>
            <span className='logout'>
              <a href='#'><i className='fas fa-sign-out-alt' title='Sign Out' aria-hidden='true' /></a>
            </span>
          </div>
        </div>
        <div className='pipelines'>
          <h1 className='pipelines-heading'>{PROJECT_NAME}//Pipelines</h1>
          <NewPipeLine onStartPipeline={this.startPipeline.bind(this)} />
          <div className='pipeline-previews'>
            { this.getPipelineCards() }
          </div>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  pipelineList: pipelines.pipelineList
})

export default connect(mapStateToProps, { selectedPipelineChanged })(Home)
