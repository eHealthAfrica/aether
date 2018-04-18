import React, { Component } from 'react'
import { connect } from 'react-redux'
import { EntityTypeViewer } from '../../components'
import { FormattedMessage } from 'react-intl'
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
          <label className='form-label'>
            <FormattedMessage
              id='entitytype.empty.message'
              defaultMessage='Paste Entity Type definitions'
            />
          </label>
          <FormattedMessage id='entityTypeSchema.placeholder' defaultMessage='Enter your schema'>
            {message => (<textarea type='text' className='monospace' value={this.state.entityTypesSchema}
              onChange={this.onSchemaTextChanged.bind(this)} placeholder={message} rows='10' />)}
          </FormattedMessage>
        </div>
      </div>
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(EntityTypes)
