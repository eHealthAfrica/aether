import React, { Component } from 'react'

export default class PaginationBar extends Component {
  render (list) {
    const {records, pageSize} = this.props
    if (records <= pageSize) {
      return <div />
    }

    const {currentPage, nextAction, previousAction} = this.props
    const numberOfPages = Math.ceil(records / pageSize)
    const pageType = (pageSize === 1 ? 'Record' : 'Page')

    return (
      <nav data-qa='data-pagination'>
        <ul className='pagination justify-content-end'>
          {
            previousAction &&
            <li className='page-item'>
              <a className='page-link' onClick={previousAction} aria-label='Previous'>
                Previous
              </a>
            </li>
          }

          <li className='page-item disabled'>
            { pageType }
            <span className='badge badge-default'>{currentPage}</span>
            of {numberOfPages}
          </li>

          {
            nextAction &&
            <li className='page-item'>
              <a className='page-link' onClick={nextAction} aria-label='Next'>
                Next
              </a>
            </li>
          }
        </ul>
      </nav>
    )
  }
}
