/* global HTMLElement */
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

/**
 * Applies supplied class to an element by id in the DOM
 */
export const applyStyle = (id, className, color) => {
  const element = document.getElementById(id)
  if (element) {
    element.classList.add(className)
    if (color) {
      element.setAttribute('style', `background-color: ${color};`)
      element.pseudoStyle('before', 'background', color)
      element.pseudoStyle('after', 'border-left', `0.6rem solid ${color}`)
    }
  }
}

/**
 * Removes supplied class from an element by id in the DOM
 */
export const removeStyle = (id, className) => {
  const element = document.getElementById(id)
  if (element) {
    element.classList.remove(className)
    element.style.backgroundColor = null
  }
}

const UID = {
  _current: 0,
  getNew: function () {
    this._current++
    return this._current
  }
}

HTMLElement.prototype.pseudoStyle = function (element, prop, value) {
  const _this = this
  const _sheetId = 'pseudoStyles'
  const _head = document.head || document.getElementsByTagName('head')[0]
  const _sheet = document.getElementById(_sheetId) || document.createElement('style')
  _sheet.id = _sheetId
  const className = `pseudoStyle${UID.getNew()}`
  _this.className += ` ${className}`
  _sheet.innerHTML += ` .${className}:${element}{${prop}:${value}}`
  _head.appendChild(_sheet)
  return this
}
