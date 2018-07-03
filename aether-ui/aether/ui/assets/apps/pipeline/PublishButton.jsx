import React, { Component } from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'
import { PROJECT_NAME } from '../utils/constants'
import { publishPipeline, selectedPipelineChanged } from './redux'
import Modal from '../components/Modal'

class PublishButton extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showPublishOptions: false,
      publishOptionsButtons: null,
      publishOptionsContent: null
    }
  }

  componentWillReceiveProps (nextProps) {
    if (nextProps.selectedPipeline && nextProps.selectedPipeline.id &&
      nextProps.selectedPipeline.id === this.props.pipeline.id) {
      if (nextProps.publishError) {
        this.getPublishOptions('error', nextProps.publishError)
      }
      if (nextProps.publishSuccess) {
        this.getPublishOptions('success', nextProps.publishSuccess)
      }
    }
  }

  buildPublishErrors (errors) {
    const errorList = []
    errors.error.forEach(error => {
      errorList.push(<li key={error}>
        <FormattedMessage id={`publish.error.${error}`} defaultMessage={error} />
      </li>)
    })
    errors.exists.forEach(exists => {
      Object.keys(exists).forEach(exist => {
        errorList.push(<li key={exist}>
          <FormattedMessage id={`publish.exists.${exist}`} defaultMessage={exists[exist]} />
        </li>)
      })
    })
    return <ul className='error'>{errorList}</ul>
  }

  buildPublishSuccess (publishSuccessList) {
    const successList = publishSuccessList.map(passed => (
      <li key={passed}>
        <FormattedMessage id={`publish.success.${passed}`} defaultMessage={passed} />
      </li>
    ))
    return <ul className='success'>{successList}</ul>
  }

  getPublishOptions (status, statusData) {
    this.setState({
      publishOptionsButtons: status === 'success' ? (
        <button type='button' className='btn btn-w btn-primary' onClick={this.setPublishOptionsModal.bind(this, false)}>
          <FormattedMessage
            id='publish.modal.sucess.ok'
            defaultMessage='Ok'
          />
        </button>
      ) : (
        <div>
          <button type='button' className='btn btn-w' onClick={this.setPublishOptionsModal.bind(this, false)}>
            <FormattedMessage
              id='publish.modal.cancel'
              defaultMessage='Cancel'
            />
          </button>
          {
            (!this.props.pipeline.mapping_errors || !this.props.pipeline.mapping_errors.length) && (<button type='button' className='btn btn-w btn-primary' onClick={this.publishOverwrite.bind(this)}>
              <FormattedMessage
                id='publish.modal.overwrite'
                defaultMessage='Overwrite Existing Pipeline'
              />
            </button>)
          }
        </div>
      ),
      showPublishOptions: true,
      publishOptionsContent: status === 'success' ? this.buildPublishSuccess(statusData) : this.buildPublishErrors(statusData)
    })
  }

  setPublishOptionsModal (visible) {
    this.setState({
      showPublishOptions: visible
    })
  }

  publishOverwrite () {
    this.setPublishOptionsModal(false)
    this.props.publishPipeline(this.props.pipeline.id, PROJECT_NAME, true)
  }

  publish () {
    this.props.selectedPipelineChanged(this.props.pipeline)
    this.props.publishPipeline(this.props.pipeline.id)
  }

  render () {
    return (
      <div>
        <Modal show={this.state.showPublishOptions} header={`Publish ${this.props.pipeline.name}`}
          buttons={this.state.publishOptionsButtons}>
          {this.state.publishOptionsContent}
        </Modal>
        <button type='button' className={this.props.className} onClick={this.publish.bind(this)}>
          <FormattedMessage
            id='pipeline.navbar.breadcrumb.publish'
            defaultMessage='Publish pipeline'
          />
        </button>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  publishError: pipelines.publishError,
  publishSuccess: pipelines.publishSuccess,
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, { publishPipeline, selectedPipelineChanged })(PublishButton)
