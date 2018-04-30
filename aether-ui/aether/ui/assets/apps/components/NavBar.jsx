import React, { Component } from 'react'
import { defineMessages, injectIntl } from 'react-intl'
import { Link } from 'react-router-dom'

import { getLoggedInUser } from '../utils'

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

        { this.props.showBreadcrumb &&
          <div data-qa='navbar-breadcrumb' className='top-nav-breadcrumb'>
            { this.props.children }
          </div>
        }

        <div data-qa='navbar-user' className='top-nav-user'>
          <span class='user-name'>
            { getLoggedInUser().name }
          </span>
          <span className='logout'>
            <a href='/accounts/logout'>
              <i className='fas fa-sign-out-alt' title={formatMessage(MESSAGES.logout)} />
            </a>
          </span>
        </div>
      </div>
    )
  }
}

export default injectIntl(NavBar)
