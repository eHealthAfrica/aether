import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'

class Output extends Component {
  render () {
    return (
      <div className='section-body'>
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
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps)(Output)
