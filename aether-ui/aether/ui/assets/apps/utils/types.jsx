import moment from 'moment'

const DATE_FORMAT = 'YYYY-MM-DD'
const DATE_REGEXP = /^(\d{4})-(\d{2})-(\d{2})$/

const TIME_FORMAT = 'HH:mm:ss'
const TIME_REGEXP = /^(\d{2}):(\d{2}):(\d{2})$/

const DATETIME_FORMAT = 'YYYY-MM-DDTHH:mm:ss.S...Z'
const DATETIME_REGEXP = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}).(\d{1,6})(\+(\d{2}):(\d{2})|Z)+$/

const checkDate = (value, regexp, format) => (value.match(regexp) && moment(value, format).isValid())

/**
 * Checks if the given string value represents a date in `YYYY-MM-DD` format
 *
 * @param {string} value
 */
export const isDate = (value) => checkDate(value, DATE_REGEXP, DATE_FORMAT)

/**
 * Checks if the given string value represents a time in `HH[24]:MM:SS` format
 *
 * @param {string} value
 */
export const isTime = (value) => checkDate(value, TIME_REGEXP, TIME_FORMAT)

/**
 * Checks if the given string value represents a date+time in ISO 8601 format
 *
 * @param {string} value
 */
export const isDateTime = (value) => checkDate(value, DATETIME_REGEXP, DATETIME_FORMAT)

/**
 * Identifies the object type.
 * Returns `null` if even being a known type it can be considered as empty
 *
 * @param {any} value
 */
export const getType = (value) => {
  const NO_TYPE = null

  // null or undefined
  if (value === null || value === undefined) {
    return NO_TYPE
  }

  if (value.toString().trim() === '') {
    return NO_TYPE
  }

  // check the object type
  switch (Object.prototype.toString.call(value)) {
    case '[object Function]':
      return NO_TYPE // we do not expect this kind of responses

    case '[object Object]':
      return Object.keys(value).length === 0 ? NO_TYPE : 'object'

    case '[object Array]':
      return value.length === 0 ? NO_TYPE : 'array'

    case '[object Number]':
      if (parseInt(value, 10) === value) {
        return 'int'
      }
      return 'float'

    case '[object Boolean]':
      return 'bool'

    case '[object Date]':
      return 'datetime'

    case '[object String]':
      // should also check if the value represents a Date/time

      // like: 2017-09-09T14:16:05.869000+01:00
      if (isDateTime(value)) {
        return 'datetime'
      }

      // like: 2017-09-09
      if (isDate(value)) {
        return 'date'
      }

      // like: 14:16:05
      if (isTime(value)) {
        return 'time'
      }

      return 'string'
  }

  return NO_TYPE
}

/**
 * Converts property name into sentence case
 * - `my_name_is` into `my name is` (snake case)
 * - `myNameIs` into `my Name Is` (camel case)
 *
 * @param {string} key
 */
export const cleanPropertyName = (key) => key
  .replace(/_/g, ' ') //             convert `my_name_is` into `my name is`
  .replace(/([A-Z]+)/g, ' $1') //    convert `myNameIs` into `my Name Is`
  .replace(/([A-Z][a-z])/g, ' $1')

/**
 * Flatten a deep object into a one level object with it’s path as key
 *
 * @param {object} object     - The object to be flattened
 * @param {string} separator  - The properties separator
 *
 * @return {object}           - The resulting flat object
 */
export const flatten = (object, separator = '.') => {
  // assumption: no property names contain `separator`
  // https://gist.github.com/penguinboy/762197#gistcomment-2168525

  const isValidObject = (value) => {
    if (!value) {
      return false
    }

    const isArray = Array.isArray(value)
    const isObject = Object.prototype.toString.call(value) === '[object Object]'
    const hasKeys = !!Object.keys(value).length

    return !isArray && isObject && hasKeys
  }

  const walker = (child, path = []) => Object.assign(
    {},
    ...Object.keys(child).map(key => (
      isValidObject(child[key])
        ? walker(child[key], path.concat([key]))
        : { [path.concat([key]).join(separator)]: child[key] }
    ))
  )

  return Object.assign({}, walker(object))
}

/**
 * Unflatten a one level object with its path as key into a deep object.
 *
 * @param {object} object     - The object to be unflattened
 * @param {string} separator  - The properties separator
 *
 * @return {object}           - The resulting unflat object
 */
export const unflatten = (object, separator = '.') => {
  const deepObject = {}
  Object.keys(object).forEach(path => {
    path.split(separator)
      .reduce((current, key, index, arr) => {
        const value = arr.length === index + 1 ? object[path] : {}
        current = current[key] = current[key] || value
        return current
      }, deepObject)
  })

  return deepObject
}

/**
 * Filter deep object properties by the allowed paths.
 *
 * @param {object} object     - The object to be filtered
 * @param {array}  paths      - The list of allowed paths
 * @param {string} separator  - The properties separator
 *
 * @return {object}           - The resulting unflat object
 */

export const filterByPaths = (object, paths, separator = '.') => {
  const flattenObject = flatten(object, separator)
  const filteredFlattenObject = {}
  Object.keys(flattenObject)
    .filter(key => paths.find(path => key.indexOf(path) === 0))
    .forEach(key => { filteredFlattenObject[key] = flattenObject[key] })
  return unflatten(filteredFlattenObject, separator)
}

/**
 * Analyze the flattened keys structure to figure out how to build a table header.
 *
 * Data
 * ====
 *
 * {
 *   a: {
 *     b: {
 *       c: 1,
 *       d: 2
 *     },
 *     e: {
 *       f: true
 *     },
 *     g: []
 *   },
 *   h: 0
 * }
 *
 *
 * Flatten keys
 * ============
 *
 * [
 *   'a.b.c',
 *   'a.b.d',
 *   'a.e.f',
 *   'a.g',
 *   'h'
 * ]
 *
 *
 * Levels
 * ======
 *
 * [
 *   // level 0
 *   {
 *     'a': { key: 'a', label: 'A', siblings: 4, hasChildren: true, isLeaf: false },
 *     'h': { key: 'h', label: 'H', siblings: 1, hasChildren: false, isLeaf: true }
 *   },
 *   // level 1
 *   {
 *     'a.b': { key: 'a.b', label: 'B', siblings: 2, hasChildren: true, isLeaf: false },
 *     'a.e': { key: 'a.e', label: 'E', siblings: 1, hasChildren: true, isLeaf: false },
 *     'a.g': { key: 'a.g', label: 'G', siblings: 1, hasChildren: false, isLeaf: true }
 *   },
 *   // level 2
 *   {
 *     'a.b.c': { key: 'a.b.c', label: 'C', siblings: 1, hasChildren: false, isLeaf: true },
 *     'a.b.d': { key: 'a.b.d', label: 'D', siblings: 1, hasChildren: false, isLeaf: true },
 *     'a.e.f': { key: 'a.e.f', label: 'F', siblings: 1, hasChildren: false, isLeaf: true }
 *   }
 * ]
 *
 *
 * Table header
 * ============
 *
 * +----------------+---+
 * | A              | H |
 * +-------+---+----+   |
 * | B     | E | G  |   |
 * +---+---+---+    |   |
 * | C | D | F |    |   |
 * +---+---+---+----+---+
 * | 1 | 2 | T | [] | 0 |
 * +---+---+---+----+---+
 *
 *
 * @param {array}  flatKeys  - The flat object keys
 * @param {string} separator - The properties separator used
 */
export const inflate = (flatKeys, separator = '.') => {
  // assumption: no property names contain `separator`

  const depth = flatKeys.reduce((acc, curr) => Math.max(acc, curr.split(separator).length), 0)
  const tree = []
  for (let level = 0; level < depth; level++) {
    tree.push({})

    // which headers are available at this level
    flatKeys
      .filter(flatKey => flatKey.split(separator).length > level)
      .map(flatKey => {
        const keys = flatKey.split(separator)
        const key = keys.filter((_, i) => i <= level).join(separator)

        return {
          key,
          label: cleanPropertyName(keys[level]),

          // replace `separator` with the common `.`
          path: key.replace(new RegExp('\\' + separator, 'g'), '.'),

          // if there are more nested properties
          hasChildren: keys.length > (level + 1),
          isLeaf: keys.length === (level + 1),

          // count the properties that start with this one (siblings at this tree level)
          // adding suffix `separator` skips the edge case
          // { a: 1, ab: { c: 1 } } -> { 'a': 1, 'ab.c': 1 }
          siblings: flatKeys.filter(c => c === key || c.indexOf(key + separator) === 0).length
        }
      })
      .forEach(column => {
        // this removes duplicates (sibling properties)
        tree[level][column.key] = column
      })
  }

  return tree
}
