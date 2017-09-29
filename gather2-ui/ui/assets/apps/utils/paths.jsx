/**
 * Returns the API url to get the Surveys data
 *
 * @param {string}  app          - app source: `core` (default) or `odk`
 * @param {number}  id           - survey id
 * @param {boolean} withStats    - include survey stats
 * @param {object}  params       - query string parameters
 */
export const getSurveysAPIPath = ({app, id, withStats, ...params}) => {
  const source = (app === 'odk' ? 'odk' : 'core')
  const stats = (source === 'core' && withStats ? '-stats' : '')

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
 * With    {surveyId} -> core/surveys/{surveyId}/responses.json?{queryString}
 * Without {surveyId} -> core/responses.json?{queryString}
 *
 * @param {number}  surveyId    - survey id
 * @param {object}  params      - query string parameters
 */
export const getResponsesAPIPath = ({surveyId, ...params}) => {
  const surveyNested = (surveyId ? `/surveys/${surveyId}` : '')
  const queryString = buildQueryString(params)

  return `/core${surveyNested}/responses.json?${queryString}`
}

/**
 * Return the REST API url
 *
 * With    {id} -> {app}/{type}/{id}.json
 * Without {id} -> {app}/{type}.json?{queryString}
 *
 * @param {string}  app         - app source: `core` or `odk`
 * @param {string}  type        - item type
 * @param {number}  id          - item id
 * @param {object}  params      - query string parameters
 */
const buildAPIPath = (app, type, id, params) => {
  if (id) {
    return `/${app}/${type}/${id}.json`
  }

  const queryString = buildQueryString(params || {})
  return `/${app}/${type}.json?${queryString}`
}

/**
 * Build the query string based on arguments
 *
 * @param {number} surveyId     - survey id
 * @param {string} search       - search text
 * @param {number} page         - current page
 * @param {number} pageSize     - page size
 */
const buildQueryString = ({surveyId, search, page, pageSize}) => {
  return (search ? `&search=${encodeURIComponent(search)}` : '') +
         (surveyId ? `&survey_id=${surveyId}` : '') +
         (page ? `&page=${page}` : '') +
         (pageSize ? `&page_size=${pageSize}` : '')
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
