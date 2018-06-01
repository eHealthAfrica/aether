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
 * Checks if the two objects are equal, comparing even nested properties.
 *
 * @param {*}      a          -- object 1
 * @param {*}      b          -- object 2
 * @param {bool}   ignoreNull -- ignore null values
 */
export const deepEqual = (a, b, ignoreNull = false) => {
  if (typeof a !== 'object') {
    return a === b
  }
  let ka = Object.keys(a)
  let kb = Object.keys(b)
  let key, i
  // ignore null and undefined values
  if (ignoreNull) {
    ka = ka.filter((x) => a[x] != null)
    kb = kb.filter((x) => b[x] != null)
  }
  // having the same number of owned properties (keys incorporates hasOwnProperty)
  if (ka.length !== kb.length) {
    return false
  }
  // the same set of keys (although not necessarily the same order),
  ka.sort()
  kb.sort()
  // cheap key test
  for (i = ka.length - 1; i >= 0; i--) {
    if (ka[i] !== kb[i]) {
      return false
    }
  }
  // equivalent values for every corresponding key, and
  // possibly expensive deep test
  for (i = ka.length - 1; i >= 0; i--) {
    key = ka[i]
    if (!deepEqual(a[key], b[key], ignoreNull)) {
      return false
    }
  }
  return true
}

/**
 * Takes the logged in user, id (int) and name, from the DOM element
 */
export const getLoggedInUser = () => {
  const loggedInUserElement = document.getElementById('logged-in-user-info')
  return {
    id: parseInt(loggedInUserElement ? loggedInUserElement.getAttribute('data-user-id') : null, 10),
    name: loggedInUserElement ? loggedInUserElement.getAttribute('data-user-name') : ''
  }
}

/* This function is used as a typeHook option by `avro.Type.forValue().
 * Background: when deriving avro schemas from sample data, all records, enums, and
 * fixed avro types will be anonymous. Using the `typeHook` option, we can pass in
 * a name generator which allows to maintain compatibility with other avro
 * libraries such as python-spavro.
 *
 *    See: https://github.com/mtth/avsc/issues/108#issuecomment-302436388
 */
export const generateSchemaName = (prefix) => {
  let index = 0
  return (schema) => {
    switch (schema.type) {
      case 'enum':
      case 'fixed':
      case 'record':
        schema.name = `${prefix}_${index++}`
        break
      default:
    }
  }
}
