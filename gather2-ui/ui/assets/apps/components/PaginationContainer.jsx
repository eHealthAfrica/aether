import React, { Component } from 'react'
import { getData } from '../utils/request'

import LoadingSpinner from './LoadingSpinner'
import FetchErrorAlert from './FetchErrorAlert'
import EmptyAlert from './EmptyAlert'
import PaginationBar from './PaginationBar'

export default class PaginationContainer extends Component {
  constructor (props) {
    super(props)

    this.state = {
      // default status variables
      pageSize: this.props.pageSize || 25,
      page: 1,
      isLoading: true,
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
        prevState.pageSize !== this.state.pageSize) {
      this.fetchData()
    }
  }

  fetchData () {
    const {page, pageSize} = this.state
    const url = `${this.props.url}&page=${page}&page_size=${pageSize}`

    getData(url)
      .then((response) => {
        this.setState({
          list: response,
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

    const position = this.props.position || 'bottom'
    const {count, results} = this.state.list
    const ListComponent = this.props.listComponent

    return (
      <div data-qa='data-loaded'>
        { count === 0 && <EmptyAlert /> }

        { (position === 'top') && this.renderPaginationBar() }

        <ListComponent
          list={results}
          total={count}
          start={this.props.pageSize * (this.state.page - 1) + 1}
        />

        { (position === 'bottom') && this.renderPaginationBar() }
      </div>
    )
  }

  renderPaginationBar (list) {
    const {count} = this.state.list
    const {page, pageSize} = this.state

    if (count <= pageSize) {
      return ''
    }

    return (
      <PaginationBar
        currentPage={page}
        pageSize={pageSize}
        records={count}
        gotToPage={this.updateCurrentPage.bind(this)}

        showFirst={this.props.showFirst}
        showPrevious={this.props.showPrevious}
        showNext={this.props.showNext}
        showLast={this.props.showLast}
      />
    )
  }

  updateCurrentPage (page) {
    this.setState({ page, isLoading: true, error: false })
  }
}
