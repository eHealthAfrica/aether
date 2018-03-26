import React, { Component } from 'react'
import { connect } from 'react-redux'

class NewPipeLine extends Component {
  constructor (props) {
    super(props)
    this.state = {
      view: 'button'
    }
  }

  render () {
    return (
      <div className='pipeline-new'>

        { this.state.view === 'button'  &&
          <button
            type='button'
            className='btn btn-d btn-big'
            onClick={() => this.setState({ view: 'form' })}>
            <span className='details-title'>New pipeline</span>
          </button>
        }

        { this.state.view === 'form'  &&
          <div className='pipeline-form'>
            <div className='form-group'>
              <input
                type='text'
                required
                name='name'
                className='text-input'
                placeholder='Name of new pipeline'
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
              onClick={() => this.setState({ view: 'button' })}>
              <span className='details-title'>Start Pipeline</span>
            </button>
          </div>
        }

      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(NewPipeLine)
