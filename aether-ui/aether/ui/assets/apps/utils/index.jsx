import avro from 'avro-js'

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
  const unknown = '--'
  const hasNestedObject = schemaObject.type && typeof schemaObject.type === 'object'
  const groupList = <div><div>{schema.name}</div><ul>{}</ul></div>
  const itemMarkUp = (<li><span>{ schemaObject.name || unknown }</span>
      {hasNestedObject ? mapSchemaObject() : ''}</li>)
  const mapSchemaObject = schemaObject => {
    if (schemaObject.fields) {
      schemaObject.fields.forEach(field => {
        schemaToMarkup(field)
      })
    } else {

    }
  }
  try {
    const validatedSchema = avro.parse(schema)

  } catch (error) {
    throw 'Invalid Schema'
  }
}

const test = schema => {
  const getChildren = () => {
    if (schema.fields.length) {

    } else if (typeof schema.type !== 'string') {

    } else {
      return (<li><span>{schema.name}</span><span>{schema.type}</span></li>)
    }
  }
  const rootObject = (<div><div>{ schema.name }</div><ul>{ getChildren() }</ul></div>)
}
