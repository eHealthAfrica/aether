import React, { Component } from 'react'
import { defineMessages, injectIntl, FormattedMessage } from 'react-intl'
import { Link } from 'react-router-dom'

import { getLoggedInUser } from '../../utils'

const MESSAGES = defineMessages({
  logout: {
    defaultMessage: 'Sign Out',
    id: 'navbar.logout'
  }
})

class NavBar extends Component {
  render () {
    const {formatMessage} = this.props.intl

    return (
      <div data-qa='navbar' className='navbar top-nav'>
        <Link className='top-nav-logo' to='/' title='aether'>
          <div className='logo-container'>
            <div className='flipper'>
              <div className='front' />
              <div className='back' />
            </div>
          </div>
          <span data-app-name='app-name'><b>ae</b>ther</span>
        </Link>

        { this.props.showBreadcrumb && this.renderBreadcrumb() }

        <div data-qa='navbar-user' className='top-nav-user'>
          { getLoggedInUser().name }
          <span className='logout'>
            <a href='/accounts/logout'>
              <i className='fas fa-sign-out-alt' title={formatMessage(MESSAGES.logout)} />
            </a>
          </span>
        </div>
      </div>
    )
  }

  renderBreadcrumb () {
    const {selectedPipeline} = this.props
    const label = selectedPipeline
      ? selectedPipeline.name
      : <FormattedMessage id='navbar.select.pipeline' defaultMessage='Select a pipeline' />

    return (
      <div data-qa='navbar-breadcrumb' className='top-nav-breadcrumb'>
        <Link to='/'>
          <FormattedMessage id='navbar.pipelines' defaultMessage='Pipelines' />
        </Link>
        <span> // {label}</span>
      </div>
    )
  }
}

export default injectIntl(NavBar)
