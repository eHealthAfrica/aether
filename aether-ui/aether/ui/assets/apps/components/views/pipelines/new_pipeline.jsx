import React, { Component } from 'react'
import { connect } from 'react-redux'
import { addPipeline, selectedPipelineChanged } from '../../../redux/modules/pipeline'
import { generateGUID } from '../../../utils/index'

class NewPipeLine extends Component {
  constructor (props) {
    super(props)
    this.state = {
      view: 'button',
      newPipelineName: ''
    }
  }

  startPipeline () {
    if (this.state.newPipelineName) {
      const newPipeline = {
        name: this.state.newPipelineName,
        id: generateGUID(),
        entityTypes: 0,
        errors: 0
      }
      this.props.addPipeline(newPipeline)
      this.props.onStartPipeline(newPipeline)
    }
  }

  render () {
    return (
      <div className='pipeline-new'>

        { this.state.view === 'button' &&
          <button
            type='button'
            className='btn btn-d btn-big'
            onClick={() => this.setState({ view: 'form' })}>
            <span className='details-title'>New pipeline</span>
          </button>
        }

        { this.state.view === 'form' &&
          <div className='pipeline-form'>
            <div className='form-group'>
              <input
                type='text'
                required
                name='name'
                className='text-input'
                placeholder='Name of new pipeline'
                value={this.state.newPipelineName}
                onChange={event => this.setState({newPipelineName: event.target.value})}
              />
              <label className='form-label'>
                Name of new pipeline
              </label>
            </div>
            <button
              type='button'
              className='btn btn-d btn-big btn-cancel'
              onClick={() => this.setState({ view: 'button' })}>
              <span className='details-title'>Cancel</span>
            </button>
            <button
              type='button'
              className='btn btn-d btn-big'
              onClick={this.startPipeline.bind(this)}>
              <span className='details-title'>Start Pipeline</span>
            </button>
          </div>
        }

      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {
  addPipeline,
  selectedPipelineChanged
})(NewPipeLine)
