import React, { Component } from 'react'
import { IntlProvider } from 'react-intl'

export default class AppIntl extends Component {
  render () {
    return (
      <IntlProvider defaultLocale='en' locale={navigator.locale || 'en'}>
        { this.props.children }
      </IntlProvider>
    )
  }
}
