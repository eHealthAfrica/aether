import React from 'react'

/**
 * Clones object.
 *
 * @param {*} x -- the object
 */
export const clone = (x) => JSON.parse(JSON.stringify(x))

/**
 * Generates random UUID
 */
export const generateGUID = () => {
  const s4 = () => {
    return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1)
  }
  return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4()
}

/**
 * Takes the logged in user, id (int) and name, from the DOM element
 */
export const getLoggedInUser = () => {
  const loggedInUserElement = document.getElementById('logged-in-user-info')
  return {
    id: parseInt(loggedInUserElement.getAttribute('data-user-id'), 10),
    name: loggedInUserElement.getAttribute('data-user-name')
  }
}

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
