import React from 'react'

/**
 * Parse avro schema to nested markup
 */
export const schemaToMarkup = schema => {
  const children = []
  if (schema.fields && schema.fields.length) {
    children.push(<ul key={schema.name}>
      <li>{schema.name}</li>
      <li>
        <ul key={schema.name}>
          {schema.fields.map(field => (schemaToMarkup(field)))}
        </ul>
      </li>
    </ul>)
  } else if (typeof schema.type !== 'string') {
    schema.type.name = schema.name
    children.push(schemaToMarkup(schema.type))
  } else {
    children.push(<li key={schema.name}>
      <span>{schema.name}</span>&nbsp;&nbsp;
      <span>{schema.type}</span>
    </li>)
  }
  return children
}
