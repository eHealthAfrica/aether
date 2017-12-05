/**
 * Returns the API url to get the Surveys data
 *
 * @param {string}  app          - app source: `kernel` (default) or `odk`
 * @param {number}  id           - survey id
 * @param {boolean} withStats    - include survey stats
 * @param {object}  params       - query string parameters
 */
export const getSurveysAPIPath = ({app, id, withStats, ...params}) => {
  const source = (app === 'odk' ? 'odk' : 'kernel')
  const stats = (source === 'kernel' && withStats ? '-stats' : '')

  return buildAPIPath(source, `surveys${stats}`, id, params)
}

/**
 * Returns the API url to get the Surveyors data
 *
 * @param {number}  id          - surveyor id
 * @param {object}  params      - query string parameters
 */
export const getSurveyorsAPIPath = ({id, ...params}) => {
  return buildAPIPath('odk', 'surveyors', id, params)
}

/**
 * Returns the API url to get the XForms data
 *
 * @param {number}  id          - xForm id *
 * @param {object}  params      - query string parameters
 */
export const getXFormsAPIPath = ({id, ...params}) => {
  return buildAPIPath('odk', 'xforms', id, params)
}

/**
 * Returns the API url to get the Responses data by survey
 *
 * With    {surveyId} -> kernel/surveys/{surveyId}/responses.json?{queryString}
 * Without {surveyId} -> kernel/responses.json?{queryString}
 *
 * @param {number}  surveyId    - survey id
 * @param {object}  params      - query string parameters
 */
export const getResponsesAPIPath = ({surveyId, ...params}) => {
  const surveyNested = (surveyId ? `/surveys/${surveyId}` : '')
  const format = params.format || 'json'
  const queryString = buildQueryString(params)

  return `/kernel${surveyNested}/responses.${format}?${queryString}`
}

/**
 * Return the REST API url
 *
 * With    {id} -> {app}/{type}/{id}.json
 * Without {id} -> {app}/{type}.json?{queryString}
 *
 * @param {string}  app         - app source: `kernel` or `odk`
 * @param {string}  type        - item type
 * @param {number}  id          - item id
 * @param {object}  params      - query string parameters
 */
const buildAPIPath = (app, type, id, params) => {
  if (id) {
    return `/${app}/${type}/${id}.json`
  }
  const format = params.format || 'json'

  const queryString = buildQueryString(params || {})
  return `/${app}/${type}.${format}?${queryString}`
}

/**
 * Build the query string based on arguments
 *
 * @param {number} surveyId     - survey id
 * @param {string} search       - search text
 * @param {number} page         - current page
 * @param {number} pageSize     - page size
 * @param {string} fields       - comma separated list of fields to include in the response
 * @param {string} omit         - comma separated list of fields to omit in the response
 */
export const buildQueryString = ({surveyId, search, page, pageSize, fields, omit}) => {
  return (search ? `&search=${encodeURIComponent(search)}` : '') +
         (surveyId ? `&mapping_id=${surveyId}` : '') +
         (page ? `&page=${page}` : '') +
         (pageSize ? `&page_size=${pageSize}` : '') +
         (fields ? `&fields=${fields}` : '') +
         (omit ? `&omit=${omit}` : '')
}

/**
 * Returns the path to go to any Surveys page
 *
 * @param {string} action       - action: `list` (default), `view`, `add`, `edit`
 * @param {number} id           - survey id
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
