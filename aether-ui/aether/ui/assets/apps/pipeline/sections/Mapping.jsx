/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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
import { FormattedMessage, defineMessages, injectIntl } from 'react-intl'
import { connect } from 'react-redux'

import { generateGUID, deepEqual, objectToString } from '../../utils'
import { updateContract } from '../redux'

const MESSAGES = defineMessages({
  mappingRuleSourcePlaceholder: {
    defaultMessage: 'define source',
    id: 'mapping.rule.source.placeholder'
  },
  mappingRuleDestinationPlaceholder: {
    defaultMessage: 'define destination',
    id: 'mapping.rule.destination.placeholder'
  },
  mappingRulesPlaceHolder: {
    defaultMessage: 'Enter your mapping rules as an array',
    id: 'mapping.rules.placeholder'
  }
})

class Mapping extends Component {
  constructor (props) {
    super(props)

    this.state = {
      mappingRules: props.contract.mapping_rules || [],
      mappingRulesInput: this.mappingToJSON(props.contract.mapping_rules || []),

      view: 'rules',
      error: null,
      jsonError: null
    }
  }

  componentDidUpdate (prevProps) {
    if (!deepEqual(prevProps.contract.mapping_rules, this.props.contract.mapping_rules)) {
      this.setState({
        mappingRules: this.props.contract.mapping_rules || [],
        mappingRulesInput: this.mappingToJSON(this.props.contract.mapping_rules || []),
        error: null,
        jsonError: null
      })
    }
  }

  JSONToMapping (rules) {
    const mappingRules = JSON.parse(rules).map(rule => ({
      id: generateGUID(),
      source: rule[0],
      destination: rule[1]
    }))

    return mappingRules
  }

  mappingToJSON (rules) {
    return objectToString(rules.map(item => ([item.source, item.destination])))
  }

  notifyChange (event) {
    event.preventDefault()
    if (this.props.contract.is_read_only) {
      return
    }
    this.props.updateContract({
      ...this.props.contract,
      mapping_rules: this.state.mappingRules,
      is_identity: false
    })
  }

  notifyChangeJSON (event) {
    event.preventDefault()
    if (this.props.contract.is_read_only) {
      return
    }

    this.setState({ jsonError: null })

    try {
      const rules = this.JSONToMapping(this.state.mappingRulesInput)
      this.props.updateContract({
        ...this.props.contract,
        mapping_rules: rules,
        is_identity: false
      })
    } catch (error) {
      this.setState({ jsonError: error.message })
    }
  }

  hasChanged () {
    return !deepEqual(this.state.mappingRules, this.props.contract.mapping_rules)
  }

  hasChangedJson () {
    try {
      return !deepEqual(JSON.parse(this.state.mappingRulesInput), this.props.contract.mapping_rules.map(rule => (
        [rule.source, rule.destination]
      )))
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
                id='mapping.toogle.rules'
                defaultMessage='Mapping rules'
              />
            </button>

            <button
              className={`tab ${this.state.view === 'definitions' ? 'selected' : ''}`}
              onClick={this.toggleMappingView.bind(this)}>
              <FormattedMessage
                id='mapping.toggle.definitions'
                defaultMessage='JSON'
              />
            </button>
          </div>

          { this.state.view === 'rules' &&
            <div className='rules'>
              <form onSubmit={this.notifyChange.bind(this)}>
                { this.state.mappingRules.map(this.renderRule.bind(this)) }

                { !this.props.contract.is_read_only &&
                  <div className='rules-buttons'>
                    { this.renderAddNewRuleButton() }

                    <button
                      type='submit'
                      className='btn btn-d btn-primary'
                      disabled={!this.hasChanged()}>
                      <span className='details-title'>
                        <FormattedMessage
                          id='mapping.rules.button.ok'
                          defaultMessage='Apply mapping rules to pipeline'
                        />
                      </span>
                    </button>
                  </div>
                }
              </form>
            </div>
          }

          { this.state.view === 'definitions' && this.renderDefinition() }
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
      <button
        type='button'
        className='btn btn-d btn-primary'
        onClick={addNewRule}>
        <FormattedMessage id='mapping.rules.button.add' defaultMessage='Add rule' />
      </button>
    )
  }

  renderRule (rule) {
    const { formatMessage } = this.props.intl

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

    const hasError = (source, destination = null) => (
      Boolean(this.props.contract.mapping_errors.find(
        error => (error.path && (error.path === source || error.path === destination))
      ))
    )

    return (
      <div key={rule.id} className={`${hasError(rule.source, rule.destination) && 'error'} rule`}>
        <div className='rule-input source'>
          <input
            type='text'
            required
            className={`${hasError(rule.source) && 'error'} input-d`}
            name='source'
            value={rule.source}
            onChange={onChangeInput}
            placeholder={formatMessage(MESSAGES.mappingRuleSourcePlaceholder)}
            disabled={this.props.contract.is_read_only}
          />
        </div>

        <div className='rule-input destination'>
          <input
            type='text'
            required
            className={`${hasError(rule.destination) && 'error'} input-d`}
            name='destination'
            value={rule.destination}
            onChange={onChangeInput}
            placeholder={formatMessage(MESSAGES.mappingRuleDestinationPlaceholder)}
            disabled={this.props.contract.is_read_only}
          />
        </div>

        { !this.props.contract.is_read_only &&
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
        }
      </div>
    )
  }

  renderDefinition () {
    const { formatMessage } = this.props.intl

    return (
      <div className='definition'>
        <form onSubmit={this.notifyChangeJSON.bind(this)}>
          <div className='textarea-header'>
            { this.state.jsonError &&
              <div className='hint error-message'>
                <h4 className='hint-title'>
                  <FormattedMessage
                    id='mapping.rules.invalid'
                    defaultMessage='You have provided invalid mapping rules.'
                  />
                </h4>
                { this.state.jsonError }
              </div>
            }
          </div>

          <textarea
            className={`input-d monospace ${this.state.error ? 'error' : ''}`}
            value={this.state.mappingRulesInput}
            onChange={this.onMappingRulesTextChanged.bind(this)}
            placeholder={formatMessage(MESSAGES.mappingRulesPlaceHolder)}
            rows='10'
            disabled={this.props.contract.is_read_only}
          />

          { !this.props.contract.is_read_only &&
            <button type='submit' className='btn btn-d btn-primary mt-3' disabled={!this.hasChangedJson()}>
              <span className='details-title'>
                <FormattedMessage
                  id='mapping.rules.button.ok'
                  defaultMessage='Apply mapping rules to pipeline'
                />
              </span>
            </button>
          }
        </form>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  contract: pipelines.currentContract
})
const mapDispatchToProps = { updateContract }

export default connect(mapStateToProps, mapDispatchToProps)(injectIntl(Mapping))
