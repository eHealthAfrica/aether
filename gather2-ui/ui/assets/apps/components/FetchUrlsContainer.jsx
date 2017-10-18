import React, { Component } from 'react'
import { fetchUrls } from '../utils/request'

import EmptyAlert from './EmptyAlert'
import FetchErrorAlert from './FetchErrorAlert'
import LoadingSpinner from './LoadingSpinner'
import RefreshSpinner from './RefreshSpinner'

/**
 * FetchUrlsContainer component.
 *
 * Request data from server and returns back to the provided component.
 *
 * Properties:
 *   `urls`:               The list of urls objects to fetch.
 *                         The expected urls format is:
 *                          [
 *                            {
 *                              name: 'string',
 *                              url: 'https://...'
 *                            },
 *                            ...
 *                          ]
 *
 *   `hideHints`:          Indicates if the auxiliary hint components
 *                         (loading, error) are hidden.
 *                         The whole fetch process is in silent mode.
 *
 *   `handleResponse`:     Function that transform the response.
 *
 *   `targetComponent`:    The rendered component after a sucessful request.
 *                         It's going to received as properties the trasformed
 *                         response and a function that allows to reload the data.
 *
 */

export default class FetchUrlsContainer extends Component {
  constructor (props) {
    super(props)

    this.state = {
      // default status variables
      isLoading: true,
      isRefreshing: false,
      error: false
    }
  }

  componentDidMount () {
    this.loadData()
  }

  refreshData () {
    this.setState({ isRefreshing: true })
    this.loadData()
  }

  loadData () {
    fetchUrls(this.props.urls)
      .then((response) => {
        const {handleResponse} = this.props
        this.setState({
          response: handleResponse ? handleResponse(response) : response,
          isLoading: false,
          isRefreshing: false,
          error: false
        })
      })
      .catch((error) => {
        console.log(error)
        this.setState({
          isLoading: false,
          isRefreshing: false,
          error: true
        })
      })
  }

  render () {
    if (this.state.isLoading) {
      return this.props.hideHints ? <div /> : <LoadingSpinner />
    }
    if (this.state.error) {
      return this.props.hideHints ? <div /> : <FetchErrorAlert />
    }
    if (!this.state.response) {
      return this.props.hideHints ? <div /> : <EmptyAlert />
    }

    const TargetComponent = this.props.targetComponent

    return (
      <div data-qa='data-loaded'>
        { this.state.isRefreshing && <RefreshSpinner /> }
        <TargetComponent
          {...this.state.response}
          reload={this.refreshData.bind(this)}
        />
      </div>
    )
  }
}
