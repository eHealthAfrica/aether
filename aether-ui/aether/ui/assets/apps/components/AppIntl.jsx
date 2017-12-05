import React, { Component } from 'react'
import { IntlProvider } from 'react-intl'

/**
 * AppIntl component.
 *
 * Wraps the children with the IntlProvider component to enable i18n and L11n.
 */

export default class AppIntl extends Component {
  render () {
    return (
      <IntlProvider defaultLocale='en' locale={navigator.locale || 'en'}>
        { this.props.children }
      </IntlProvider>
    )
  }
}
