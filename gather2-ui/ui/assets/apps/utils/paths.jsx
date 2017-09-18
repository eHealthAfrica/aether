/**
 * Returns the API url to get the Surveys data
 *
 * @param {number} id
 * @param {boolean} withStats
 * @param {string} search
 */
export const getSurveysAPIPath = ({id, withStats, search}) => {
  const idPart = (id ? `/${id}` : '')
  const stats = (withStats ? '-stats' : '')
  const queryString = (!id && search ? `search=${encodeURIComponent(search)}` : '')

  return `/core/surveys${stats}${idPart}.json?${queryString}`
}

/**
 * Returns the API url to get the Surveyors data
 *
 * @param {number} id
 * @param {number} surveyId
 * @param {string} search
 */
export const getSurveyorsAPIPath = ({id, surveyId, search}) => {
  const idPart = (id ? `/${id}` : '')
  const queryString = (!id && search ? `search=${encodeURIComponent(search)}` : '') +
                      (!id && surveyId ? `&survey_id=${surveyId}` : '')

  return `/odk/surveyors${idPart}.json?${queryString}`
}

/**
 * Returns the API url to get the XForms data by survey
 *
 * @param {number} surveyId
 * @param {string} search
 */
export const getXFormsAPIPath = ({surveyId, search}) => {
  const queryString = (search ? `search=${encodeURIComponent(search)}` : '') +
                      (surveyId ? `&survey_id=${surveyId}` : '')

  return `/odk/xforms.json?${queryString}`
}

/**
 * Returns the API url to get the Responses data by survey
 *
 * @param {number} surveyId
 */
export const getResponsesAPIPath = ({surveyId}) => {
  const surveyPart = (surveyId ? `/surveys/${surveyId}` : '')

  return `/core${surveyPart}/responses.json?`
}

/**
 * Returns the path to go to any Surveys page
 *
 * @param {string} action
 * @param {number} id
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
 * @param {string} action
 * @param {number} id
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
