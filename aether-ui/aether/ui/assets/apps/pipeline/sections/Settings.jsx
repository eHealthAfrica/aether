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
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { updateContract } from '../redux'
import { isEmpty } from '../../utils'
import { deriveEntityTypes, deriveMappingRules } from '../../utils/avro-utils'

import { Modal } from '../../components'
import ContractPublishButton from '../components/ContractPublishButton'
import SubmissionCard from '../components/SubmissionCard'

export class IdentityMapping extends Component {
  constructor (props) {
    super(props)

    this.state = {
      showModal: false
    }
  }

  render () {
    return (
      <React.Fragment>
        <div className='identity-mapping'>
          <p>
            <FormattedMessage
              id='settings.identity.help-1'
              defaultMessage='You can use an identity contract to leave submitted data unchanged.'
            />
            &nbsp;
            <FormattedMessage
              id='settings.identity.help-2'
              defaultMessage='This will automatically create both Entity Types and Mappings.'
            />
          </p>
          <button
            data-qa='contract.identity.button.apply'
            className='btn btn-d'
            onClick={() => { this.setState({ showModal: true }) }}
            disabled={this.props.contract.is_read_only}
          >
            <FormattedMessage
              id='settings.identity.button'
              defaultMessage='Create identity contract'
            />
          </button>
        </div>

        { this.state.showModal && this.renderModal() }
      </React.Fragment>
    )
  }

  generateIdentityMapping () {
    const schema = this.props.inputSchema
    const mappingRules = deriveMappingRules(schema)
    const entityTypes = deriveEntityTypes(schema)

    this.props.updateContract({
      ...this.props.contract,
      mapping_rules: mappingRules,
      entity_types: entityTypes
    })

    this.setState({ showModal: false })
  }

  renderModal () {
    const header = (
      <FormattedMessage
        id='settings.identity.header'
        defaultMessage='Create identity contract'
      />
    )

    const buttons = (
      <div>
        <button
          data-qa='contract.identity.button.confirm'
          className='btn btn-w btn-primary'
          onClick={this.generateIdentityMapping.bind(this)}>
          <FormattedMessage
            id='settings.identity.button.confirm'
            defaultMessage='Yes'
          />
        </button>

        <button className='btn btn-w' onClick={() => { this.setState({ showModal: false }) }}>
          <FormattedMessage
            id='settings.identity.button.cancel'
            defaultMessage='Cancel'
          />
        </button>
      </div>
    )

    return (
      <Modal header={header} buttons={buttons}>
        <FormattedMessage
          id='settings.identity.content.question'
          defaultMessage='Are you sure that you want to create an identity contract?'
        />
        <FormattedMessage
          id='settings.identity.content.warning'
          defaultMessage='This action will overwrite any entity types and mappings that you have created in this contract.'
        />
      </Modal>
    )
  }
}

class Settings extends Component {
  constructor (props) {
    super(props)

    this.state = {
      contractName: props.contract.name
    }
  }

  componentDidUpdate (prevProps) {
    if (prevProps.contract.name !== this.props.contract.name) {
      this.setState({ contractName: this.props.contract.name })
    }
  }

  render () {
    const { contract } = this.props
    const showIdentityOption = (!contract.is_read_only && !isEmpty(this.props.inputSchema))

    return (
      <div className='pipeline-settings'>
        <div
          className='btn-icon close-button'
          onClick={() => this.props.onClose()}>
          <i className='fas fa-times' />
          <FormattedMessage
            id='settings.button.close'
            defaultMessage='close settings'
          />
        </div>

        <div className='contract-form'>
          <div className='form-group'>
            <label className='form-label'>
              <FormattedMessage
                id='settings.contract.name'
                defaultMessage='Contract name'
              />
            </label>
            <div className='row'>
              <div className='col'>
                <input
                  type='text'
                  required
                  name='name'
                  className='input-d contract-name'
                  value={this.state.contractName}
                  onChange={(e) => { this.setState({ contractName: e.target.value }) }}
                  disabled={contract.is_read_only}
                />
              </div>
            </div>
          </div>

          { showIdentityOption && <IdentityMapping {...this.props} /> }

          <div className='settings-section'>
            <div>
              <label className='form-label'>
                <FormattedMessage
                  id='settings.puplish.status'
                  defaultMessage='Publish status'
                />
              </label>
              <ContractPublishButton
                contract={contract}
                className='btn btn-d btn-publish'
              />
            </div>

            { contract.published_on &&
              <div className='mt-4'>
                <SubmissionCard
                  mappingset={this.props.mappingset}
                  inputData={this.props.inputData}
                />
              </div>
            }
          </div>

          { !contract.is_read_only &&
            <button
              className='btn btn-d btn-primary btn-big'
              onClick={() => {
                this.props.updateContract({
                  ...contract,
                  name: this.state.contractName
                })
                this.props.onClose()
              }}>
              <span className='details-title'>
                <FormattedMessage
                  id='settings.contract.save'
                  defaultMessage='Save'
                />
              </span>
            </button>
          }
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  mappingset: pipelines.currentPipeline.mappingset,
  inputData: pipelines.currentPipeline.input,
  inputSchema: pipelines.currentPipeline.schema,

  contract: pipelines.currentContract
})
const mapDispatchToProps = { updateContract }

export default connect(mapStateToProps, mapDispatchToProps)(Settings)
