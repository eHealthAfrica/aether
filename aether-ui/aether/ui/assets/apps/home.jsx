import 'bootstrap/dist/css/bootstrap.min.css'
import '../css/index.scss'

import React from 'react'
import { render } from 'react-dom'
import { Provider } from 'react-redux'
import { hot } from 'react-hot-loader'

import createStore from './redux/store'
import App from './components/layouts'

const appElement = document.getElementById('home-app')

const store = createStore()
const component = (
  <Provider store={store}>
    <div>
      <App />
    </div>
  </Provider>
)

render(component, appElement)

// Include this to enable HMR for this module
hot(module)(component)
