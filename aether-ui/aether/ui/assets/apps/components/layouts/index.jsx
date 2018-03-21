import React from 'react'
import { HashRouter, Switch, Route } from 'react-router-dom'
import AppLayout from './app_layout'

const App = () => (
  <HashRouter>
    <Switch>
      <Route path='/' component={AppLayout} />
    </Switch>
  </HashRouter>
)

export default App
