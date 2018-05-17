import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'

class Output extends Component {
  buildPublishErrors (errors) {
    const errorList = []
    errors.error.forEach(error => {
      errorList.push(<li key={error}>
          <FormattedMessage id={`publish.error.${error}`} defaultMessage={error} />
        </li>)
    })
    errors.exists.forEach(exists => {
      errorList.push(<li key={exists}>
          <FormattedMessage id={`publish.error.${exists}`} defaultMessage={exists} />
        </li>)
    })
    return <ul>{errorList}</ul>
  }

  buildPublishSuccess (success) {
    const successList = []
    success.forEach(passed => {
      successList.push(<li key={passed}>
          <FormattedMessage id={`publish.success.${passed}`} defaultMessage={passed} />
        </li>)
    })
    return <ul>{successList}</ul>
  }

  render () {
    return (
      <div className='section-body'>
        {
          this.props.publishError && (
            <div className='pipeline-errors'>
              <h3 className='title-medium'>
                <FormattedMessage id='publish.errors' defaultMessage='Publish errors' />
              </h3>
                {
                  this.buildPublishErrors(this.props.publishError)
                }
            </div>
          )
        }
        {
          this.props.publishSuccess && (
            <div className='pipeline-success'>
              <h3 className='title-medium'>
                <FormattedMessage id='publish.success' defaultMessage='Publish success' />
              </h3>
                {
                  this.buildPublishSuccess(this.props.publishSuccess)
                }
            </div> 
          )
        }              
        <div className='pipeline-data pipeline-errors'>
          <h3 className='title-medium'>
            <FormattedMessage id='output.mapping_errors' defaultMessage='Mapping errors' />
          </h3>
          <code>
            { JSON.stringify(this.props.selectedPipeline.mapping_errors || [], 0, 2) }
          </code>
        </div>
        <div className='pipeline-data'>
          <h3 className='title-medium'>
            <FormattedMessage id='output.data' defaultMessage='Output.data' />
          </h3>
          <code>
            { JSON.stringify(this.props.selectedPipeline.output || [], 0, 2) }
          </code>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline,
  publishError: pipelines.publishError,
  publishSuccess: pipelines.publishSuccess
})

export default connect(mapStateToProps)(Output)
