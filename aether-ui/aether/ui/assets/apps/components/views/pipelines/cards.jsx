import React from 'react'

const PipelineCard = ({ pipeline, onSelect }) => {
  return (
    <div
      onClick={() => onSelect()}
      className='pipeline-preview'>
      <h2 className='preview-heading'>{pipeline.name}</h2>
      <div className='summary-entity-types'>
        <span className='badge badge-b badge-big'>{pipeline.entityTypes}</span>
        Entity-Types
      </div>
      <div className='summary-errors'>
        <span className='badge badge-b badge-big'>{pipeline.errors}</span>
        Errors
      </div>
    </div>
  )
}

export default PipelineCard
