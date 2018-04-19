import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'
import { EntityTypeViewer } from '../../components'

class EntityTypes extends Component {
  constructor (props) {
    super(props)

    this.state = {
      entityTypesSchema: JSON.stringify(this.props.entityTypes, 0, 2)
    }
  }

  componentWillReceiveProps (nextProps) {
    this.setState({
      entityTypesSchema: JSON.stringify(nextProps.entityTypes, 0, 2)
    })
  }

  onSchemaTextChanged (event) {
    this.setState({
      entityTypesSchema: event.target.value
    })
  }

  notifyChange (event) {
    const newEntityTypes = JSON.parse(this.state.entityTypesSchema)
    this.props.onChange(newEntityTypes)
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
            {message => (
              <textarea
                className='monospace'
                value={this.state.entityTypesSchema}
                onChange={this.onSchemaTextChanged.bind(this)}
                onBlur={this.notifyChange.bind(this)}
                placeholder={message}
                rows='10'
              />
            )}
          </FormattedMessage>
        </div>
      </div>
    )
  }
}

export default connect()(EntityTypes)
