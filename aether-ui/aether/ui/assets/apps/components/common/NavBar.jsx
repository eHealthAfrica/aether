import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { Link } from 'react-router-dom'

class NavBar extends Component {
  render () {
    return (
      <div className='navbar top-nav'>
        <a className='top-nav-logo' href='/' title='aether'>
          <div className='logo-container'>
            <div className='flipper'>
              <div className='front' />
              <div className='back' />
            </div>
          </div>
          <span data-app-name='app-name'><b>ae</b>ther</span>
        </a>
        {this.props.showBreadcrumb && 
          <div className='top-nav-breadcrumb'>
            <Link to='/'>
            <FormattedMessage
              id='navbar.piplines'
              defaultMessage='PIPELINES' />
            </Link>
            <span> // {this.props.selectedPipeline ? this.props.selectedPipeline.name : 'Select a pipeline'}</span>
          </div>
        }
        <div className='top-nav-user'>
          <span
            id='logged-in-user-info'>
            {this.props.username || 'Username'}
          </span>
          <span className='logout'>
            <a href='#'><i className='fa fa-sign-out' title='Sign Out' aria-hidden='true' /></a>
          </span>
        </div>
      </div>
    )
  }
}

export default NavBar