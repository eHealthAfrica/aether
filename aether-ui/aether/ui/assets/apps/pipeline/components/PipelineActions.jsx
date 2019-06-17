import React from 'react'

import PipelineOptions from './PipelineOptions'
import ContractAddButton from './ContractAddButton'

const PipelineActions = props => (
  <div className='pipeline-actions'>
    <PipelineOptions
      delete={props.delete}
      rename={props.rename}
    />
    <ContractAddButton pipeline={props.pipeline} history={props.history} />
  </div>
)

export default PipelineActions
