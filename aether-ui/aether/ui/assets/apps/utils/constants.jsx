import urls from './urls'

// MAX_PAGE_SIZE ==> used as a hack to return all records via api
// calls pending when pagination is fully implemented
export const MAX_PAGE_SIZE = 5000
export const PROJECT_NAME = 'AUX'

const types = {
  GET_KERNEL_URL: 'get_kernel_url',
  GET_KERNEL_URL_ERROR: 'get_kernel_url_error'
}

const INITIAL_CONST = {
  kernelUrl: ''
}

export const getKernelURL = () => ({
  types: ['', types.GET_KERNEL_URL, ''],
  promise: client => client.get(urls.KERNEL_URL)
})

const reducer = (state = INITIAL_CONST, action) => {
  switch (action.type) {
    case types.GET_KERNEL_URL: {
      return { ...state, kernelUrl: action.payload }
    }

    default:
      return state
  }
}

export default reducer
