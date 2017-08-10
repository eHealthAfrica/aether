import React, { Component } from 'react'
import { fetchUrls } from '../utils/request'

import LoadingSpinner from './LoadingSpinner'
import FetchErrorAlert from './FetchErrorAlert'
import EmptyAlert from './EmptyAlert'

export default class FetchUrlsContainer extends Component {
  constructor (props) {
    super(props)

    this.state = {
      // default status variables
      isLoading: true,
      error: false
    }
  }

  componentDidMount () {
    fetchUrls(this.props.urls)
      .then((response) => {
        this.setState({
          response: response,
          isLoading: false,
          error: false
        })
      })
      .catch((error) => {
        console.log(error)
        this.setState({
          isLoading: false,
          error: true
        })
      })
  }

  render () {
    if (this.state.isLoading) {
      return <LoadingSpinner />
    }
    if (this.state.error) {
      return <FetchErrorAlert />
    }
    if (!this.state.response) {
      return <EmptyAlert />
    }

    return (
      <div data-qa='data-loaded'>
        { React.cloneElement(this.props.children, {...this.state.response}) }
      </div>
    )
  }
}
