import React, { Component } from 'react'
import { Provider } from 'react-redux'
import { IntlProvider } from 'react-intl'
import { HashRouter, Switch, Route } from 'react-router-dom'

import createStore from '../redux/store'

const store = createStore()

export default class AppLayout extends Component {
  render () {
    return (
      <Provider store={store}>
        <IntlProvider defaultLocale='en' locale={navigator.locale || 'en'}>
          <HashRouter>
            <Switch>
              <Route path='/' component={this.props.app} />
            </Switch>
          </HashRouter>
        </IntlProvider>
      </Provider>
    )
  }
}
