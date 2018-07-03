import ApiClient from '../../utils/api'

const apiClient = new ApiClient()

export default () => next => action => {
  const { promise, types, ...rest } = action
  if (!promise) {
    return next(action)
  }

  const [REQUEST, SUCCESS, FAILURE] = types
  next({ ...rest, type: REQUEST })
  return promise(apiClient)
    .then(payload => {
      next({ ...rest, payload, type: SUCCESS })
    })
    .catch(err => {
      const error = { message: err.message, error: err.error, status: err.status }
      next({ ...rest, error, type: FAILURE })
    })
}
