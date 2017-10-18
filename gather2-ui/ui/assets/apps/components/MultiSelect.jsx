import React, { Component } from 'react'
import { defineMessages, injectIntl } from 'react-intl'
import FilteredMultiSelect from 'react-filtered-multiselect'

const MESSAGES = defineMessages({
  select: {
    defaultMessage: 'Add',
    id: 'multiselect.select'
  },
  deselect: {
    defaultMessage: 'Remove',
    id: 'multiselect.deselect'
  },
  filter: {
    defaultMessage: 'Type…',
    id: 'multiselect.filter'
  }
})

/**
 * MultiSelect component.
 *
 * Renders a multi-select component similar to Django MultiSelect widget.
 * https://github.com/insin/react-filtered-multiselect
 */

export class MultiSelect extends Component {
  constructor (props) {
    super(props)

    this.state = {
      values: props.values || [],

      valueProp: this.props.valueProp || 'id',
      textProp: this.props.textProp || 'name'
    }
  }

  componentDidUpdate (prevProps, prevState) {
    if (prevState.values !== this.state.values) {
      this.props.onChange(this.state.values)
    }
  }

  render () {
    const {formatMessage} = this.props.intl

    return (
      <div className='row'>
        <div className='col-6'>
          <FilteredMultiSelect
            buttonText={formatMessage(MESSAGES.select)}
            placeholder={formatMessage(MESSAGES.filter)}

            selectedOptions={this.state.values}
            options={this.props.options}
            valueProp={this.state.valueProp}
            textProp={this.state.textProp}

            onChange={this.onSelect.bind(this)}

            size={6}
            classNames={{
              filter: 'form-control',
              select: 'form-control',
              button: 'btn btn-block btn-secondary',
              buttonActive: 'btn btn-block btn-secondary'
            }}
          />
        </div>
        <div className='col-6'>
          <FilteredMultiSelect
            buttonText={formatMessage(MESSAGES.deselect)}
            placeholder={formatMessage(MESSAGES.filter)}

            options={this.state.values}
            valueProp={this.state.valueProp}
            textProp={this.state.textProp}

            onChange={this.onDeselect.bind(this)}

            size={6}
            classNames={{
              filter: 'form-control',
              select: 'form-control',
              button: 'btn btn-block btn-secondary',
              buttonActive: 'btn btn-block btn-secondary'
            }}
          />
        </div>
      </div>
    )
  }

  onSelect (values) {
    let v = [...new Set([...this.state.values, ...values])]
    v.sort((a, b) => a[this.state.valueProp] - b[this.state.valueProp])
    this.setState({ values: v })
  }

  onDeselect (values) {
    const removeIds = values.map(value => value[this.state.valueProp])
    this.setState({
      values: this.state.values
        .filter(value => removeIds.indexOf(value[this.state.valueProp]) === -1)
    })
  }
}

// Include this to enable `this.props.intl` for this component.
export default injectIntl(MultiSelect)
