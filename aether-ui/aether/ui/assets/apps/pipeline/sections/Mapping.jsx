import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'
import { generateGUID } from '../../utils'

class Mapping extends Component {
  constructor (props) {
    super(props)

    this.state = {
      mappingRules: this.parseProps(props)
    }
  }

  componentWillReceiveProps (nextProps) {
    this.setState({
      mappingRules: this.parseProps(nextProps)
    })
  }

  parseProps (props) {
    return props.selectedPipeline.mapping || []
  }

  notifyChange (event) {
    event.preventDefault()
    this.props.onChange(this.state.mappingRules)
  }

  render () {
    return (
      <div className='section-body'>
        <div className='rules'>
          { this.renderAddNewRuleButton() }

          <form onSubmit={this.notifyChange.bind(this)}>
            { this.state.mappingRules.map(this.renderRule.bind(this)) }

            <button type='submit' className='btn btn-d btn-big mt-2'>
              <span className='details-title'>
                <FormattedMessage
                  id='mapping.rules.button.ok'
                  defaultMessage='Apply mapping rules to pipeline'
                />
              </span>
            </button>
          </form>
        </div>

        { this.renderDefinition() }
      </div>
    )
  }

  renderAddNewRuleButton () {
    const addNewRule = () => {
      this.setState({
        mappingRules: [
          ...this.state.mappingRules,
          // add to bottom
          {
            id: generateGUID(),
            source: '',
            destination: ''
          }
        ]
      })
    }

    return (
      <button type='button' className='btn btn-d btn-big mb-4' onClick={addNewRule}>
        <FormattedMessage id='mapping.button.add' defaultMessage='Add rule' />
      </button>
    )
  }

  renderRule (rule) {
    const modifyRule = (rule) => {
      this.setState({
        mappingRules: this.state.mappingRules.map(r => r.id !== rule.id ? r : rule)
      })
    }

    const removeRule = () => {
      this.setState({
        mappingRules: this.state.mappingRules.filter(r => r.id !== rule.id)
      })
    }

    const onChangeInput = (event) => {
      modifyRule({
        ...rule,
        [event.target.name]: event.target.value
      })
    }

    return (
      <div key={rule.id} className='m-2'>
        <FormattedMessage id='mapping.rule.source.placeholder' defaultMessage='define source'>
          {message => (
            <input
              type='text'
              required
              className='monospace'
              name='source'
              value={rule.source}
              onChange={onChangeInput}
              placeholder={message}
            />
          )}
        </FormattedMessage>

        <FormattedMessage id='mapping.rule.destination.placeholder' defaultMessage='define destination'>
          {message => (
            <input
              type='text'
              required
              className='monospace'
              name='destination'
              value={rule.destination}
              onChange={onChangeInput}
              placeholder={message}
            />
          )}
        </FormattedMessage>

        <button
          type='button'
          className='btn btn-d btn-cancel'
          onClick={removeRule}>
          <span className='details-title'>
            <FormattedMessage
              id='mapping.rule.button.delete'
              defaultMessage='Remove'
            />
          </span>
        </button>
      </div>
    )
  }

  renderDefinition () {
    const definition = {
      // include mapping rules as expected in kernel
      mapping: (this.props.selectedPipeline.mapping || [])
        .map(rule => ([rule.source, rule.destination])),
      mapping_errors: this.props.selectedPipeline.errors || []
    }

    return (
      <div className='definition'>
        <h3>
          <FormattedMessage id='mapping.definitions' defaultMessage='Rule definitions' />
        </h3>
        <code>
          { JSON.stringify(definition, 0, 2) }
        </code>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps)(Mapping)
