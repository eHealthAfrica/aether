/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import React, { Component } from 'react'
import { defineMessages, injectIntl } from 'react-intl'

import { getLoggedInUser } from '../utils'

const MESSAGES = defineMessages({
  logout: {
    defaultMessage: 'Sign Out',
    id: 'navbar.logout'
  }
})

class NavBar extends Component {
  render () {
    const { showLogo, showBreadcrumb, children, intl: { formatMessage } } = this.props
    const user = getLoggedInUser()
    const { origin, pathname } = window.location
    const logoutUrl = `${origin}${pathname}logout`

    return (
      <div data-qa='navbar' className='navbar top-nav'>
        {
          showLogo && (
            <a href={origin} className='top-nav-logo' title='aether'>
              <div className='logo-container'>
                <div className='flipper'>
                  <div className='front' />
                  <div className='back' />
                </div>
              </div>
              <span data-app-name='app-name'><b>ae</b>ther</span>
            </a>
          )
        }

        {
          showBreadcrumb &&
            <div data-qa='navbar-breadcrumb' className='top-nav-breadcrumb'>
              {children}
            </div>
        }

        <div data-qa='navbar-user' className='top-nav-user'>
          <span className='user-name'>
            {user.name}
          </span>
          <span className='logout'>
            <a href={logoutUrl}>
              <i className='fas fa-sign-out-alt' title={formatMessage(MESSAGES.logout)} />
            </a>
          </span>
        </div>
      </div>
    )
  }
}

export default injectIntl(NavBar)
