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
import { updatePipeline } from '../redux'

class Mapping extends Component {
  constructor (props) {
    super(props)

    this.state = {
      mappingRules: props.selectedPipeline.mapping || [],
      view: 'rules'
    }
  }

  componentWillReceiveProps (nextProps) {
    this.setState({
      mappingRules: nextProps.selectedPipeline.mapping || []
    })
  }

  notifyChange (event) {
    event.preventDefault()
    this.props.updatePipeline({ ...this.props.selectedPipeline, mapping: this.state.mappingRules })
  }

  hasChanged () {
    return !deepEqual(this.state.mappingRules, this.props.selectedPipeline.mapping)
  }

  toggleMappingView () {
    if (this.state.view === 'rules') {
      this.setState({ view: 'definitions' })
    } else {
      this.setState({ view: 'rules' })
    }
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
