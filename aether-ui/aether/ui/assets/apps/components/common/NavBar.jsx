import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'

class NavBar extends Component {
  render () {
    return (
      <div data-qa='navbar' className='navbar top-nav'>
        <a className='top-nav-logo' href='/' title='aether'>
          <div className='logo-container'>
            <div className='flipper'>
              <div className='front' />
              <div className='back' />
            </div>
          </div>
          <span data-app-name='app-name'><b>ae</b>ther</span>
        </a>

        { this.props.showBreadcrumb && this.renderBreadcrumb() }

        <div data-qa='navbar-user' className='top-nav-user'>
          <span
            id='logged-in-user-info'>
            {this.props.username || 'Username'}
          </span>
          <span className='logout'>
            <a href='/logout'>
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
        <a href='/'>
          <FormattedMessage id='navbar.pipelines' defaultMessage='PIPELINES' />
        </a>
        <span> // {label}</span>
      </div>
    )
  }
}

export default NavBar
