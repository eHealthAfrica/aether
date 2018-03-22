import 'bootstrap/dist/css/bootstrap.min.css'
import '../css/index.scss'

import React from 'react'
import { render } from 'react-dom'
import { Provider } from 'react-redux'
import createStore from './redux/store'
import App from './components/layouts'

const appElement = document.getElementById('home-app')

const store = createStore()

render(
  <Provider store={store}>
    <div>
      <App />
    </div>
  </Provider>,
  appElement
)
