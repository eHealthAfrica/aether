import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { Link } from 'react-router-dom'

class NavBar extends Component {
  render () {
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
          {/* FIXME!!! take username from Django */}
          <span
            id='logged-in-user-info'>
            {this.props.username || 'Username'}
          </span>
          <span className='logout'>
            <a href='/accounts/logout'>
              <i className='fas fa-sign-out-alt' title='Sign Out' aria-hidden='true' />
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
          <FormattedMessage id='navbar.pipelines' defaultMessage='PIPELINES' />
        </Link>
        <span> // {label}</span>
      </div>
    )
  }
}

export default NavBar
