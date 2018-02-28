import React from 'react'
import ReactDOM from 'react-dom'
import { AppIntl } from './components'

if (module.hot) {
  module.hot.accept()
}

const appElement = document.getElementById('home-app')

ReactDOM.render(<div>Aether UI</div>, appElement)
