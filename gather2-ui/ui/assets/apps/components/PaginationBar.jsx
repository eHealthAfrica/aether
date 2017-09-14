import React, { Component } from 'react'
import {
  defineMessages,
  injectIntl,
  FormattedMessage,
  FormattedNumber
} from 'react-intl'

const MESSAGES = defineMessages({
  previous: {
    defaultMessage: 'Previous',
    id: 'pagination.previous'
  },
  next: {
    defaultMessage: 'Next',
    id: 'pagination.next'
  },
  record: {
    defaultMessage: 'Record {current} of {total}',
    id: 'pagination.type.record'
  },
  page: {
    defaultMessage: 'Page {current} of {total}',
    id: 'pagination.type.page'
  }
})

export class PaginationBar extends Component {
  render (list) {
    const {records, pageSize} = this.props
    if (records <= pageSize) {
      return <div />
    }

    const {formatMessage} = this.props.intl
    const {currentPage, nextAction, previousAction} = this.props
    const numberOfPages = Math.ceil(records / pageSize)
    const current = (
      <span data-qa='data-pagination-page' className='badge badge-default'>
        <FormattedNumber value={currentPage} />
      </span>
    )
    const total = (
      <span data-qa='data-pagination-total'>
        <FormattedNumber value={numberOfPages} />
      </span>
    )

    return (
      <nav data-qa='data-pagination'>
        <ul className='pagination'>
          {
            previousAction &&
            <li data-qa='data-pagination-previous' className='page-item'>
              <a
                className='page-link'
                onClick={previousAction}
                aria-label={formatMessage(MESSAGES.previous)}>
                <FormattedMessage {...MESSAGES.previous} />
              </a>
            </li>
          }

          <li className='page-item disabled'>
            <FormattedMessage
              {...MESSAGES[(pageSize === 1 ? 'record' : 'page')]}
              values={{ current, total }}
            />
          </li>

          {
            nextAction &&
            <li data-qa='data-pagination-next' className='page-item'>
              <a
                className='page-link'
                onClick={nextAction}
                aria-label={formatMessage(MESSAGES.next)}>
                <FormattedMessage {...MESSAGES.next} />
              </a>
            </li>
          }
        </ul>
      </nav>
    )
  }
}

// Include this to enable `this.props.intl` for this component.
export default injectIntl(PaginationBar)
