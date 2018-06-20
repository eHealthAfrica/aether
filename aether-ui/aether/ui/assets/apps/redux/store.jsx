import { createStore, applyMiddleware } from 'redux'
import { composeWithDevTools } from 'redux-devtools-extension'

import reducers from './reducers'
import middleware from './middleware'

export default () => {
  if (process.env.NODE_ENV !== 'production') {
    // configure store for development environment
    const enhancer = composeWithDevTools(applyMiddleware(...middleware))
    const store = createStore(reducers, enhancer)

    if (module.hot) {
      module.hot.accept('./reducers', () => {
        store.replaceReducer(require('./reducers').default)
      })
    }
    return store
  }

  return createStore(reducers, applyMiddleware(...middleware))
}
