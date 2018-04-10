import React from 'react'
import { render } from 'react-dom'
import { Provider } from 'react-redux'
import { hot } from 'react-hot-loader'
import { IntlProvider } from 'react-intl'

import createStore from './redux/store'
import App from './components/layouts'

const appElement = document.getElementById('home-app')

const store = createStore()
const component = (
  <Provider store={store}>
    <IntlProvider locale='en'>
      <App />
    </IntlProvider>
  </Provider>
)

render(component, appElement)

// Include this to enable HMR for this module
hot(module)(component)
