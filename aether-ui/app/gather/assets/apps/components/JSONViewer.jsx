import React, { Component } from 'react'
import {
  FormattedDate,
  FormattedMessage,
  FormattedNumber,
  FormattedTime
} from 'react-intl'

import { cleanPropertyName, getType } from '../utils/types'

const renderEmptyValue = () => {
  return (
    <span className='empty'>
      –
    </span>
  )
}

/**
 * JSONViewer component.
 *
 * Renders a JSON object in "pretty" format.
 */

export default class JSONViewer extends Component {
  render () {
    const {data} = this.props

    return (
      <div data-qa='json-data' className='data'>
        { this.renderValue(data) }
      </div>
    )
  }

  renderValue (value) {
    if (!getType(value)) {
      return renderEmptyValue()
    }

    // check the object type
    switch (getType(value)) {
      case 'array':
        return this.renderArray(value)

      case 'object':
        return this.renderObject(value)

      case 'int':
        return this.renderInteger(value)

      case 'float':
        return this.renderFloat(value)

      case 'bool':
        return this.renderBoolean(value)

      case 'datetime':
        return this.renderDateTime(value)

      case 'date':
        return this.renderDate(value)

      case 'time':
        // special case with `react-intl`, it needs the full date with time
        // workaround: print it as it comes
        return this.renderString(value)

      default:
        return this.renderString(value)
    }
  }

  renderString (value) {
    return <span className='value'>{value}</span>
  }

  renderInteger (value) {
    return (
      <span title={value}>
        <FormattedNumber value={value} />
      </span>
    )
  }

  renderFloat (value) {
    return (
      <span title={value}>
        <FormattedNumber
          value={value}
          style='decimal'
          minimumFractionDigits={6}
        />
      </span>
    )
  }

  renderDateTime (value) {
    return (
      <span title={value}>
        { this.renderDate(value) }
        { ' - '}
        { this.renderTime(value) }
      </span>
    )
  }

  renderDate (value) {
    return <FormattedDate
      value={value}
      year='numeric'
      month='long'
      day='numeric'
    />
  }

  renderTime (value) {
    return <FormattedTime
      value={value}
      hour12={false}
      hour='2-digit'
      minute='2-digit'
      second='2-digit'
      timeZoneName='short'
    />
  }

  renderBoolean (value) {
    return (value
      ? <FormattedMessage id='json.viewer.boolean.true' defaultMessage='Yes' />
      : <FormattedMessage id='json.viewer.boolean.false' defaultMessage='No' />
    )
  }

  renderArray (values) {
    return <JSONArrayViewer values={values} />
  }

  renderObject (value) {
    return (
      <div>
        {
          Object.keys(value).map(key => (
            <div key={key} className={`property ${getType(value[key]) || ''}`}>
              <div className={`property-title ${getType(value[key]) ? '' : 'empty'}`}>
                { cleanPropertyName(key) }
              </div>
              <div className='property-value'>
                { this.renderValue(value[key]) }
              </div>
            </div>
          ))
        }
      </div>
    )
  }
}

class JSONArrayViewer extends Component {
  constructor (props) {
    super(props)
    this.state = {
      collapsed: true
    }
  }

  render () {
    const {collapsed} = this.state
    const {values} = this.props

    if (!getType(values)) {
      return renderEmptyValue()
    }

    if (collapsed) {
      return (
        <div>
          <button
            className='btn icon-only btn-expand'
            onClick={this.toggleView.bind(this)}>
            <i className='fa fa-plus' />
          </button>

          <span className='badge'>
            <FormattedNumber value={values.length} />
          </span>
        </div>
      )
    }

    return (
      <div>
        <button
          className='btn icon-only btn-collapse'
          onClick={this.toggleView.bind(this)}>
          <i className='fa fa-minus' />
        </button>
        <ol className='property-list'>

          {
            values.map((value, index) => (
              <li key={index} className='property-item'>
                <JSONViewer data={value} />
              </li>
            ))
          }
        </ol>
      </div>
    )
  }

  toggleView () {
    this.setState({ collapsed: !this.state.collapsed })
  }
}
