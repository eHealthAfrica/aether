import ApiClient from '../../utils/api';

const apiClient = new ApiClient();

export default () => next => action => {
  const { promise, types, ...rest } = action;
  if (!promise) {
    return next(action);
  }

  const [REQUEST, SUCCESS, FAILURE] = types;
  next({ ...rest, type: REQUEST });
  const actionPromise = promise(apiClient);
  actionPromise
    .then(
      result => {
        next({ ...rest, result, type: SUCCESS });
      },
      error => {
        next({ ...rest, error, type: FAILURE });
      }
    )
    .catch(error => {
      next({ ...rest, error, type: FAILURE });
    });
  return actionPromise;
};