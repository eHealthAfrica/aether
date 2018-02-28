import jQuery from 'jquery'
import { KERNEL_APP, ODK_APP, GATHER_APP } from './constants'

const API_PREFIX = ''
const APPS = [ KERNEL_APP, ODK_APP, GATHER_APP ]

/**
 * Returns the API url to get the Mappings/Surveys data
 *
 * Internally in Aether the concept is Mapping but in Gather it refers to Survey.
 *
 * @param {string}  app          - app source: `kernel` (default), `odk` or `gather`
 * @param {number}  id           - mapping/survey id
 * @param {boolean} withStats    - include mapping/survey stats?
 * @param {object}  params       - query string parameters
 */
export const getSurveysAPIPath = ({app, id, withStats, ...params}) => {
  const source = (APPS.indexOf(app) === -1 ? KERNEL_APP : app)
  const stats = (source === KERNEL_APP && withStats ? '-stats' : '')

  let projectId
  if (app === KERNEL_APP && !params.id) {
    // Include project id in call
    projectId = jQuery('[data-qa=project-id]').val()
  }

  return buildAPIPath(source, `mappings${stats}`, id, {...params, projectId})
}

export const getProjectAPIPath = () => {
  return '/gather/project/'
}

/**
 * Returns the API url to get the Surveyors data
 *
 * @param {number}  id          - surveyor id
 * @param {object}  params      - query string parameters
 */
export const getSurveyorsAPIPath = ({id, ...params}) => {
  return buildAPIPath(ODK_APP, 'surveyors', id, params)
}

/**
 * Returns the API url to get the XForms data
 *
 * @param {number}  id          - xForm id
 * @param {object}  params      - query string parameters
 */
export const getXFormsAPIPath = ({id, ...params}) => {
  return buildAPIPath(ODK_APP, 'xforms', id, params)
}

/**
 * Returns the API url to get the Media Files data
 *
 * @param {number}  id          - Media file id *
 * @param {object}  params      - query string parameters
 */
export const getMediaFileAPIPath = ({id, ...params}) => {
  return buildAPIPath(ODK_APP, 'media-files', id, params)
}

/**
 * Returns the API url to get the Submissions data by Survey
 *
 * @param {number}  id          - Submission id
 * @param {object}  params      - query string parameters
 */
export const getSubmissionsAPIPath = ({id, ...params}) => {
  return buildAPIPath(KERNEL_APP, 'submissions', id, params)
}

/**
 * Returns the API url to get the Masks data
 *
 * @param {number}  id          - mask id *
 * @param {object}  params      - query string parameters
 */
export const getMasksAPIPath = ({id, ...params}) => {
  return buildAPIPath(GATHER_APP, 'masks', id, params)
}

/**
 * Return the REST API url
 *
 * If format is "json"
 *
 * With    {id} -> {app}/{type}/{id}.json?{queryString}
 * Without {id} -> {app}/{type}.json?{queryString}
 *
 * If format is not "json" (special case that allows to use POST to fetch data)
 *
 * With    {id} -> {app}/{type}/{id}/details.{format}?{queryString}
 * Without {id} -> {app}/{type}/fetch.{format}?{queryString}
 *
 * @param {string}  app         - app source: `kernel`, `odk` or `gather`
 * @param {string}  type        - item type
 * @param {number}  id          - item id
 * @param {string}  format      - response format
 * @param {object}  params      - query string parameters
 */
const buildAPIPath = (app, type, id, {format = 'json', ...params}) => {
  const suffix = (
    (id ? '/' + id : '') +
    // suffix with the "post as get" friendly option
    (format !== 'json' ? '/' + (id ? 'details' : 'fetch') : '')
  )
  const queryString = id ? '' : buildQueryString(params)
  return `${API_PREFIX}/${app}/${type}${suffix}.${format}?${queryString}`
}

/**
 * Builds the query string based on arguments
 */
export const buildQueryString = (params = {}) => (
  Object
    .keys(params)
    .filter(key => (
      params[key] !== undefined &&
      params[key] !== null &&
      params[key].toString().trim() !== ''
    ))
    .map(key => ([
      // transforms `key` from camelCase (js convention) into snake_case (python convention)
      key.replace(/(.)([A-Z]+)/g, '$1_$2').toLowerCase(),
      // encodes `value` to use it in URL addresses
      encodeURIComponent(params[key])
    ]))
    .map(([key, value]) => `${key}=${value}`)
    .join('&')
)

/**
 * Returns the path to go to any Surveys page
 *
 * @param {string} action       - action: `list` (default), `view`, `add`, `edit`
 * @param {number} id           - mapping/survey id
 */
export const getSurveysPath = ({action, id}) => {
  switch (action) {
    case 'edit':
      if (id) {
        return `/surveys/edit/${id}`
      }
      return '/surveys/add/'

    case 'add':
      return '/surveys/add/'

    case 'view':
      if (id) {
        return `/surveys/view/${id}`
      }
      return '/surveys/list/'

    default:
      return '/surveys/list/'
  }
}

/**
 * Returns the path to go to any Surveyors page
 *
 * @param {string} action       - action: `list` (default), `add`, `edit`
 * @param {number} id           - surveyor id
 */
export const getSurveyorsPath = ({action, id}) => {
  switch (action) {
    case 'edit':
      if (id) {
        return `/surveyors/edit/${id}`
      }
      return '/surveyors/add/'

    case 'add':
      return '/surveyors/add/'

    default:
      return '/surveyors/list/'
  }
}
