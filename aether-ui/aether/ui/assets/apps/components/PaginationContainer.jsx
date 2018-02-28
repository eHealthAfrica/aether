import React, { Component } from 'react'
import { getData } from '../utils/request'
import { buildQueryString } from '../utils/paths'

import EmptyAlert from './EmptyAlert'
import FetchErrorAlert from './FetchErrorAlert'
import LoadingSpinner from './LoadingSpinner'
import PaginationBar from './PaginationBar'
import RefreshSpinner from './RefreshSpinner'

/**
 * PaginationContainer component.
 *
 * Request paginated data from server and returns back to the provided component.
 *
 * Properties:
 *   `url`:               The url to fetch, should allow `page` and `page_size` parameters.
 *   `pageSize`:          The page size. Default to 25.
 *   `listComponent`:     The rendered component after a sucessful request.
 *                        It's going to received as properties the list of results,
 *                        the total number of results and the position number
 *                        of the first element.
 *   `position`:          Where to display the pagination bar regarding the list
 *                        component. Possible values: `top` and `bottom` (default).
 *   `search`:            Indicates if the search option it's enable.
 *   `showXxx`:           Indicates if the button `Xxx` (`First` , `Previous`, `Next`, `Last`)
 *                        is shown in the pagination bar.
 *   `extras`:            An object that passes directly to the listComponent.
 *
 */

export default class PaginationContainer extends Component {
  constructor (props) {
    super(props)

    this.state = {
      // default status variables
      pageSize: this.props.pageSize || 25,
      page: 1,
      isLoading: true,
      isRefreshing: false,
      error: false
    }
  }

  componentWillReceiveProps (nextProps) {
    if (nextProps.pageSize !== this.state.pageSize) {
      this.setState({ pageSize: nextProps.pageSize, page: 1 })
    }
  }

  componentDidMount () {
    this.fetchData()
  }

  componentDidUpdate (prevProps, prevState) {
    if (prevState.page !== this.state.page ||
        prevState.pageSize !== this.state.pageSize ||
        prevState.search !== this.state.search) {
      this.fetchData()
    }
  }

  fetchData () {
    const {page, pageSize, search} = this.state
    const url = `${this.props.url}&${buildQueryString({page, pageSize, search})}`

    getData(url)
      .then((response) => {
        this.setState({
          list: response,
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
      return <LoadingSpinner />
    }
    if (this.state.error) {
      return <FetchErrorAlert />
    }

    const position = this.props.position || 'bottom'
    const {count, results} = this.state.list
    const ListComponent = this.props.listComponent

    return (
      <div data-qa='data-loaded'>
        { this.state.isRefreshing && <RefreshSpinner /> }
        { (position === 'top') && this.renderPaginationBar() }

        { count === 0 && <EmptyAlert /> }

        <ListComponent
          {...this.props.extras}
          list={results}
          total={count}
          start={this.state.pageSize * (this.state.page - 1) + 1}
        />

        { (position === 'bottom') && this.renderPaginationBar() }
      </div>
    )
  }

  renderPaginationBar (list) {
    const {count} = this.state.list
    const {page, pageSize} = this.state

    return (
      <PaginationBar
        currentPage={page}
        pageSize={pageSize}
        records={count}
        goToPage={(page) => { this.setState({ page, isRefreshing: true }) }}
        onSearch={(search) => { this.setState({ search, page: 1, isRefreshing: true }) }}

        search={this.props.search}
        showFirst={this.props.showFirst}
        showPrevious={this.props.showPrevious}
        showNext={this.props.showNext}
        showLast={this.props.showLast}
      />
    )
  }
}
