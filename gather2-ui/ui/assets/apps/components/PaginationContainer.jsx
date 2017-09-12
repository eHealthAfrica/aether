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

  componentDidMount () {
    this.fetchData()
  }

  componentDidUpdate (prevProps, prevState) {
    if (prevState.page !== this.state.page) {
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

        <ListComponent list={results} />

        { (position === 'bottom') && this.renderPaginationBar() }
      </div>
    )
  }

  renderPaginationBar (list) {
    const {count, next, previous} = this.state.list
    const {page, pageSize} = this.state

    if (count <= pageSize) {
      return ''
    }

    let nextAction
    if (next) {
      nextAction = (evt) => { this.updateCurrentPage(evt, page + 1) }
    }

    let prevAction
    if (previous) {
      prevAction = (evt) => { this.updateCurrentPage(evt, page - 1) }
    }

    return (
      <PaginationBar
        currentPage={page}
        pageSize={pageSize}
        records={count}
        previousAction={prevAction}
        nextAction={nextAction}
      />
    )
  }

  updateCurrentPage (event, page) {
    event.preventDefault()
    this.setState({ page, isLoading: true, error: false })
  }
}
