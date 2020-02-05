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

import React, { useState, useEffect } from 'react'
import { FormattedMessage, defineMessages, injectIntl } from 'react-intl'
import { connect } from 'react-redux'

import { ViewsBar } from '../../components'
import { generateGUID, deepEqual, objectToString } from '../../utils'
import { updateContract } from '../redux'

const LIST_VIEW = 'LIST_VIEW'
const JSON_VIEW = 'JSON_VIEW'

const MESSAGES = defineMessages({
  listView: {
    defaultMessage: 'Mapping rules',
    id: 'mapping.rules.view.list'
  },
  sourcePlaceholder: {
    defaultMessage: 'Define source',
    id: 'mapping.rule.source.placeholder'
  },
  destinationPlaceholder: {
    defaultMessage: 'Define destination',
    id: 'mapping.rule.destination.placeholder'
  },

  jsonView: {
    defaultMessage: 'JSON',
    id: 'mapping.rules.view.json'
  },
  jsonPlaceholder: {
    defaultMessage: 'Enter your mapping rules as an array',
    id: 'mapping.rules.json.placeholder'
  }
})

const jsonToList = (rules) => (
  JSON.parse(rules)
    .map(rule => ({
      id: generateGUID(),
      source: rule[0],
      destination: rule[1]
    }))
)

const listToJson = (rules) => (
  objectToString((rules || []).map(item => ([item.source, item.destination])))
)

const errorsToString = (errors) => {
  if (!errors || errors.length === 0) return null

  return errors.map((err) => {
    if (Object.prototype.toString.call(err) === '[object Object]') {
      // { "description": "ddd", "path": "p" }
      // { "description": "ddd", ... }
      return err.description + (err.path ? ` "${err.path}"` : '')
    }
    return err.toString()
  })
}

const Mapping = ({
  contract,
  updateContract,
  intl: { formatMessage }
}) => {
  const [view, setView] = useState(LIST_VIEW)

  const rules = contract.mapping_rules || []
  const [prevRules, setPrevRules] = useState(rules)
  const [rulesList, setRulesList] = useState(rules)
  const [rulesJson, setRulesJson] = useState(listToJson(rules))
  const [jsonError, setJsonError] = useState(null)
  const errors = errorsToString(contract.mapping_errors)

  const updateRules = (newRules) => {
    setRulesList(newRules)
    setRulesJson(listToJson(newRules))
    setJsonError(null)
  }

  useEffect(() => {
    if (!deepEqual(prevRules, rules)) {
      setPrevRules(rules)
      updateRules(rules)
    }
  })

  const renderButtons = (disabled) => (
    contract.is_read_only
      ? ''
      : (
        <div className='action-buttons'>
          <button
            type='submit'
            className='btn btn-d btn-primary mt-3'
            disabled={disabled}
          >
            <span className='details-title'>
              <FormattedMessage
                id='mapping.rules.button.ok'
                defaultMessage='Apply mapping rules to pipeline'
              />
            </span>
          </button>

          <button
            type='button'
            className='btn btn-d btn-default'
            onClick={() => { updateRules(prevRules) }}
            disabled={disabled}
          >
            <span className='details-title'>
              <FormattedMessage
                id='mapping.rules.button.reset'
                defaultMessage='Revert unsaved changes'
              />
            </span>
          </button>
        </div>
      )
  )

  const renderRulesList = () => {
    const handleSubmit = (event) => {
      event.preventDefault()
      event.stopPropagation()
      if (contract.is_read_only) {
        return
      }

      updateContract({ ...contract, mapping_rules: rulesList, is_identity: false })
    }

    const addNewRule = () => {
      setRulesList([
        ...rulesList,
        // add to bottom
        {
          id: generateGUID(),
          source: '',
          destination: ''
        }
      ])
    }

    const hasError = (paths) => (
      Boolean(contract.mapping_errors.find(err => paths.indexOf(err.path) > -1))
    )

    const renderRule = (rule) => {
      const modifyRule = (changedRule) => {
        setRulesList(rulesList.map(r => r.id !== changedRule.id ? r : changedRule))
      }

      const removeRule = () => {
        setRulesList(rulesList.filter(r => r.id !== rule.id))
      }

      const handleChange = (event) => {
        modifyRule({ ...rule, [event.target.name]: event.target.value })
      }

      return (
        <div key={rule.id} className={`${hasError([rule.source, rule.destination]) && 'error'} rule`}>
          <div className='rule-input source'>
            <input
              type='text'
              required
              className={`${hasError([rule.source]) && 'error'} input-d`}
              name='source'
              value={rule.source}
              onChange={handleChange}
              placeholder={formatMessage(MESSAGES.sourcePlaceholder)}
              disabled={contract.is_read_only}
            />
          </div>

          <div className='rule-input destination'>
            <input
              type='text'
              required
              className={`${hasError([rule.destination]) && 'error'} input-d`}
              name='destination'
              value={rule.destination}
              onChange={handleChange}
              placeholder={formatMessage(MESSAGES.destinationPlaceholder)}
              disabled={contract.is_read_only}
            />
          </div>

          {
            !contract.is_read_only &&
              <button
                type='button'
                className='btn btn-d btn-flat btn-transparent'
                onClick={removeRule}
              >
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

    return (
      <div className='rules'>
        <form onSubmit={handleSubmit}>
          {rulesList.map(renderRule)}

          {
            !contract.is_read_only &&
              <div key='add' className='rule'>
                <div />

                <button
                  type='button'
                  className='btn btn-d btn-flat btn-transparent'
                  onClick={addNewRule}
                >
                  <span className='details-title'>
                    <FormattedMessage
                      id='mapping.rule.button.add'
                      defaultMessage='Add'
                    />
                  </span>
                </button>
              </div>
          }

          {renderButtons(deepEqual(rulesList, prevRules))}
        </form>
      </div>
    )
  }

  const renderRulesJson = () => {
    const handleSubmit = (event) => {
      event.preventDefault()
      event.stopPropagation()
      if (contract.is_read_only) {
        return
      }

      setJsonError(null)
      try {
        const rules = jsonToList(rulesJson)
        updateContract({ ...contract, mapping_rules: rules, is_identity: false })
      } catch (err) {
        setJsonError(err.message)
      }
    }

    let hasChanged = false
    try {
      hasChanged = !deepEqual(rulesJson, listToJson(prevRules))
    } catch (err) {
      hasChanged = true
    }

    return (
      <div className='definition'>
        <form onSubmit={handleSubmit}>
          <textarea
            className={`input-d monospace ${errors || jsonError ? 'error' : ''}`}
            value={rulesJson}
            onChange={(event) => {
              setRulesJson(event.target.value)
              setJsonError(null)
            }}
            placeholder={formatMessage(MESSAGES.jsonPlaceholder)}
            rows='10'
            disabled={contract.is_read_only}
          />

          {renderButtons(!hasChanged)}
        </form>
      </div>
    )
  }

  return (
    <div className='section-body'>
      <div className='toggleable-content'>
        <ViewsBar
          current={view}
          setView={setView}
          views={[
            { id: LIST_VIEW, label: formatMessage(MESSAGES.listView) },
            { id: JSON_VIEW, label: formatMessage(MESSAGES.jsonView) }
          ]}
        />

        <div className='textarea-header'>
          {
            (errors || jsonError) &&
              <div className='hint error-message'>
                <h4 className='hint-title'>
                  <FormattedMessage
                    id='mapping.rules.invalid'
                    defaultMessage='You have provided invalid mapping rules.'
                  />
                </h4>
                <ul>
                  {
                    /* show json error only in JSON view */
                    view === JSON_VIEW && jsonError &&
                      <li key='json-error'>{jsonError}</li>
                  }
                  {
                    /* show common errors in list view or if there is no json error */
                    (view === LIST_VIEW || !jsonError) &&
                    errors &&
                      errors.map((err, index) => <li key={index}>{err}</li>)
                  }
                </ul>
              </div>
          }
        </div>

        {view === LIST_VIEW && renderRulesList()}
        {view === JSON_VIEW && renderRulesJson()}
      </div>
    </div>
  )
}

const mapStateToProps = ({ pipelines }) => ({
  contract: pipelines.currentContract
})
const mapDispatchToProps = { updateContract }

export default connect(mapStateToProps, mapDispatchToProps)(injectIntl(Mapping))
