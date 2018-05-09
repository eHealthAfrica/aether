import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'

import { generateGUID, deepEqual, applyStyle, removeStyle } from '../../utils'
import { updatePipeline } from '../redux'

class Mapping extends Component {
  constructor (props) {
    super(props)

    this.state = {
      mappingRules: this.parseProps(props)
    }
    this.setMappingStyles()
  }

  componentWillReceiveProps (nextProps) {
    if (nextProps.selectedPipeline.mapping !== this.props.selectedPipeline.mapping) {
      this.clearMappingStyles(this.props.selectedPipeline.mapping)
    }
    this.setState({
      mappingRules: this.parseProps(nextProps)
    })
    this.setMappingStyles()
  }

  setMappingStyles () {
    Object.keys(this.state.mappingRules).forEach(mapping => {
      const mappingData = this.state.mappingRules[mapping]
      applyStyle(`input_${mappingData.source}`, 'input-mapped')
      applyStyle(`entityType_${mappingData.destination}`, 'entityType-mapped')
    })
  }

  clearMappingStyles (mappings) {
    Object.keys(mappings).forEach(mapping => {
      const mappingData = mappings[mapping]
      removeStyle(`input_${mappingData.source}`, 'input-mapped')
      removeStyle(`entityType_${mappingData.destination}`, 'entityType-mapped')
    })
  }

  parseProps (props) {
    return props.selectedPipeline.mapping || []
  }

  notifyChange (event) {
    event.preventDefault()
    this.props.updatePipeline({ ...this.props.selectedPipeline, mapping: this.state.mappingRules })
  }

  hasChanged () {
    return !deepEqual(this.state.mappingRules, this.props.selectedPipeline.mapping)
  }

  render () {
    return (
      <div className='section-body'>
        <div className='rules'>
          <h3 className='title-medium'>
            <FormattedMessage id='mapping.rules' defaultMessage='Mapping rules' />
          </h3>
          <form onSubmit={this.notifyChange.bind(this)}>
            { this.state.mappingRules.map(this.renderRule.bind(this)) }

            <div className='rules-buttons'>
              { this.renderAddNewRuleButton() }

              <button type='submit' className='btn btn-d btn-primary' disabled={!this.hasChanged()}>
                <span className='details-title'>
                  <FormattedMessage
                    id='mapping.rules.button.ok'
                    defaultMessage='Apply mapping rules to pipeline'
                  />
                </span>
              </button>
            </div>
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
      <button type='button' className='btn btn-d btn-primary' onClick={addNewRule}>
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
      removeStyle(`input_${rule.source}`, 'input-mapped')
      removeStyle(`entityType_${rule.destination}`, 'entityType-mapped')
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
      <div key={rule.id} className='rule'>
        <div className='rule-input source'>
          <FormattedMessage id='mapping.rule.source.placeholder' defaultMessage='define source'>
            {message => (
              <input
                type='text'
                required
                className='input-d'
                name='source'
                value={rule.source}
                onChange={onChangeInput}
                placeholder={message}
              />
            )}
          </FormattedMessage>
        </div>

        <div className='rule-input destination'>
          <FormattedMessage id='mapping.rule.destination.placeholder' defaultMessage='define destination'>
            {message => (
              <input
                type='text'
                required
                className='input-d'
                name='destination'
                value={rule.destination}
                onChange={onChangeInput}
                placeholder={message}
              />
            )}
          </FormattedMessage>
        </div>

        <button
          type='button'
          className='btn btn-d btn-flat btn-transparent'
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
        .map(rule => ([rule.source, rule.destination]))
    }

    return (
      <div className='definition'>
        <h3 className='title-medium'>
          <FormattedMessage id='mapping.definitions' defaultMessage='Rule definitions' />
        </h3>
        <div className='definition-code'>
          <code>
            { JSON.stringify(definition, 0, 2) }
          </code>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, { updatePipeline })(Mapping)
