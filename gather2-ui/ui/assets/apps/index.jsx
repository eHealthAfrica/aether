import React from 'react'
import ReactDOM from 'react-dom'

// Include this to enable HMR for this module
if (module.hot) {
  module.hot.accept()
}

/*
This is the first page
*/

ReactDOM.render(
  <div data-qa='index'>Welcome to Gather2 UI!</div>,
  document.getElementById('index-app')
)
