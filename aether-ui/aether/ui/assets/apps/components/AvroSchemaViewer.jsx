import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import avro from 'avsc'

class AvroSchemaViewer extends Component {
  schemaToMarkup (schema) {
    const children = []
    if (schema.fields && schema.fields.length) {
      children.push(<ul key={schema.name} className='group'>
        <li data-qa={`group-title-${schema.name}`} className='group-title'>{schema.name}</li>
        <li>
          <ul key={schema.name} className='group-list'>
            {schema.fields.map(field => (this.schemaToMarkup(field)))}
          </ul>
        </li>
      </ul>)
    } else if (typeof schema.type !== 'string') {
      schema.type.name = schema.name
      children.push(this.schemaToMarkup(schema.type))
    } else {
      children.push(<li data-qa={`no-children-${schema.name}`} key={schema.name}>
        <span className='name'>{schema.name}</span>
        <span className='type'> {schema.type}</span>
      </li>)
    }
    return children
  }

  render () {
    if (!this.props.schema || !Object.keys(this.props.schema).length) {
      return (<div className='hint'>
        <FormattedMessage
          id='pipeline.input.empty.message'
          defaultMessage='Your schema for this pipeline will be displayed here once you have added a valid source.'
        />
      </div>)
    }

    try {
      avro.parse(this.props.schema, { noAnonymousTypes: true })
      return (
        <div className='input-schema'>
          { this.schemaToMarkup(this.props.schema) }
        </div>
      )
    } catch (error) {
      return (<div className='hint'>
        <FormattedMessage
          id='pipeline.input.invalid.message'
          defaultMessage='You have provided an invalid AVRO schema.'
        />
      </div>)
    }
  }
}

export default AvroSchemaViewer
