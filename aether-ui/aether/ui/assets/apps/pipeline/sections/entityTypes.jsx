import React, { Component } from 'react'
import { connect } from 'react-redux'
import { EntityTypeViewer } from '../../components'
import MockEntitytypesSchema from '../../mock/schema_entityTypes.mock'

class EntityTypes extends Component {
  constructor (props) {
    super(props)

    this.state = {
      entityTypesSchema: JSON.stringify(MockEntitytypesSchema)
    }
  }

  onSchemaTextChanged (event) {
    this.setState({
      entityTypesSchema: event.target.value
    })
  }

  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          <EntityTypeViewer schema={this.state.entityTypesSchema} />
        </div>
        <div className='section-right'>
          <label className='form-label'>paste Entity Type definitions</label>
          <textarea type='text' className='monospace' value={this.state.entityTypesSchema} onChange={this.onSchemaTextChanged.bind(this)} placeholder='Enter your schema'
            rows='10' />
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(EntityTypes)
