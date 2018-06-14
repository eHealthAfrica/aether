import React, { Component } from 'react'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'
import moment from 'moment'
import Modal from '../components/Modal'
import { generateGUID } from '../utils'

class InfoButton extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showInfo: false
    }
  }

  setInfoModal (visible) {
    this.setState({
      showInfo: visible
    })
  }

  render () {
    const { kernel_refs: kernelRefs } = this.props.pipeline
    const submissionUrl = kernelRefs && kernelRefs.mapping &&
    `${this.props.kernelUrl}/submissions/?mapping=${kernelRefs.mapping}`
    const sampleData = {
      mapping: kernelRefs && kernelRefs.mapping,
      map_revision: generateGUID(),
      revision: generateGUID(),
      payload: this.props.pipeline.input || {}
    }
    return (
      <span>
        <Modal show={this.state.showInfo} header={this.props.pipeline.name}
          buttons={<button type='button' className='btn btn-w btn-primary' onClick={this.setInfoModal.bind(this, false)}>
            <FormattedMessage
              id='info.modal.ok'
              defaultMessage='Ok'
            />
          </button>}>
          {
            submissionUrl
              ? (
                <div>
                  <div>
                    <span>
                      <FormattedMessage
                        id='info.modal.publishedDate'
                        defaultMessage={`Published on ${moment(this.props.pipeline.published_on).format('DD MMMM, YYYY HH:mm:ss')}`}
                      />
                    </span>
                  </div>
                  <br />
                  <div>
                    <span>
                      <FormattedMessage
                        id='info.modal.SubmissionUrl'
                        defaultMessage='Submission URL: '
                      />
                    </span>
                    <a href={submissionUrl}>{submissionUrl}</a>
                  </div>
                  <br />
                  <div>
                    <span>
                      <FormattedMessage
                        id='info.modal.SubmissionSample'
                        defaultMessage='Submission sample data: '
                      />
                    </span>
                    <div className='code'>
                      <code>
                        { JSON.stringify(sampleData || [], 0, 2) }
                      </code>
                    </div>
                  </div>
                </div>
              ) : (
                <span>
                  <FormattedMessage
                    id='info.modal.NotPublished'
                    defaultMessage='Pipeline is not published yet'
                  />
                </span>
              )
          }
        </Modal>
        <img src='/static/images/fullscreen-icon.svg' onClick={this.setInfoModal.bind(this, true)} />
      </span>
    )
  }
}

const mapStateToProps = ({ constants }) => ({
  kernelUrl: constants.kernelUrl
})

export default connect(mapStateToProps, {})(InfoButton)
