/*
 * Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'

import { generateGUID, deepEqual } from '../../utils'
import { updateContract } from '../redux'

class Mapping extends Component {
  constructor (props) {
    super(props)

    this.state = {
      mappingRules: props.contract.mapping || [],
      view: 'rules',
      error: null,
      mappingRulesInput: props.contract.mapping
        ? this.mappingToJSON(props.contract.mapping) : JSON.stringify([]),
      current_rules: [],
      jsonError: null
    }
  }

  componentDidMount () {
    this.setState({
      current_rules: JSON.parse(this.state.mappingRulesInput)
    })
  }

  componentWillReceiveProps (nextProps) {
    this.setState({
      mappingRules: nextProps.contract.mapping || []
    })
    if (nextProps.contract.mapping !== this.props.contract.mapping) {
      this.setState({
        current_rules: [...nextProps.contract.mapping],
        mappingRulesInput: this.mappingToJSON(nextProps.contract.mapping)
      })
    }
  }

  JSONToMapping (json) {
    try {
      const mapping = JSON.parse(json).map(rule => ({
        id: generateGUID(),
        source: rule[0],
        destination: rule[1]
      }))
      return mapping
    } catch (error) {
      throw error
    }
  }

  mappingToJSON (mapping) {
    return JSON.stringify(mapping.map(item => ([item.source, item.destination])), 0, 2)
  }

  notifyChange (event) {
    event.preventDefault()
    this.props.updateContract({ ...this.props.contract, mapping: this.state.mappingRules })
  }

  notifyChangeJSON (event) {
    event.preventDefault()
    let rules = []
    this.setState({ jsonError: null })
    try {
      rules = this.JSONToMapping(this.state.mappingRulesInput)
      this.props.updateContract({ ...this.props.contract, mapping: rules })
      this.setState({ current_rules: JSON.parse(this.state.mappingRulesInput) })
    } catch (error) {
      this.setState({ jsonError: error.message })
    }
  }

  hasChanged () {
    return !deepEqual(this.state.mappingRules, this.props.contract.mapping)
  }

  hasChangedJson () {
    try {
      return !deepEqual(JSON.parse(this.state.mappingRulesInput), this.state.current_rules)
    } catch (error) {
      return true
    }
  }

  toggleMappingView () {
    if (this.state.view === 'rules') {
      this.setState({ view: 'definitions' })
    } else {
      this.setState({ view: 'rules' })
    }
  }

  onMappingRulesTextChanged (event) {
    this.setState({ mappingRulesInput: event.target.value })
  }

  render () {
    return (
      <div className='section-body'>
        <div className='toggleable-content'>
          <div className='tabs'>
            <button
              className={`tab ${this.state.view === 'rules' ? 'selected' : ''}`}
              onClick={this.toggleMappingView.bind(this)}>
              <FormattedMessage
                id='pipeline.mapping.toggle.rules'
                defaultMessage='Mapping rules'
              />
            </button>
            <button
              className={`tab ${this.state.view === 'definitions' ? 'selected' : ''}`}
              onClick={this.toggleMappingView.bind(this)}>
              <FormattedMessage
                id='pipeline.mapping.toggle.definitions'
                defaultMessage='JSON'
              />
            </button>
          </div>

          {this.state.view === 'rules' &&
            <div className='rules'>
              <form onSubmit={this.notifyChange.bind(this)}>
                { this.state.mappingRules.map(this.renderRule.bind(this)) }

                <div className='rules-buttons'>
                  { this.renderAddNewRuleButton() }

                  <button type='submit' className='btn btn-d btn-primary' disabled={this.props.contract.is_read_only || !this.hasChanged()}>
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
          }

          {this.state.view === 'definitions' &&
            this.renderDefinition()
          }

        </div>
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
      <button type='button' className='btn btn-d btn-primary' onClick={addNewRule} disabled={this.props.contract.is_read_only}>
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

    const hasError = (source, destination = null) => (Boolean(this.props.contract.mapping_errors.find(
      error => (error.path && (error.path === source || error.path === destination))
    )))

    return (
      <div key={rule.id} className={`${hasError(rule.source, rule.destination) && 'error'} rule`}>
        <div className='rule-input source'>
          <FormattedMessage id='mapping.rule.source.placeholder' defaultMessage='define source'>
            {message => (
              <input
                type='text'
                required
                className={`${hasError(rule.source) && 'error'} input-d`}
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
                className={`${hasError(rule.destination) && 'error'} input-d`}
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
          onClick={removeRule}
          disabled={this.props.contract.is_read_only}>
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
    return (
      <div className='definition'>
        <form onSubmit={this.notifyChangeJSON.bind(this)}>

          <div className='textarea-header'>
            { this.state.jsonError &&
              <div className='hint error-message'>
                <h4 className='hint-title'>
                  <FormattedMessage
                    id='mapping.invalid.message'
                    defaultMessage='You have provided invalid mapping rules.'
                  />
                </h4>
                { this.state.jsonError }
              </div>
            }
          </div>

          <FormattedMessage id='mappingRules.placeholder' defaultMessage='Enter your mapping rules as an array'>
            {message => (
              <textarea
                className={`input-d monospace ${this.state.error ? 'error' : ''}`}
                value={this.state.mappingRulesInput}
                onChange={this.onMappingRulesTextChanged.bind(this)}
                placeholder={message}
                rows='10'
                disabled={this.props.contract.is_read_only}
              />
            )}
          </FormattedMessage>

          <button type='submit' className='btn btn-d btn-primary mt-3' disabled={!this.hasChangedJson()}>
            <span className='details-title'>
              <FormattedMessage
                id='mapping.button.ok'
                defaultMessage='Apply mapping rules to pipeline'
              />
            </span>
          </button>
        </form>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, { updateContract })(Mapping)
