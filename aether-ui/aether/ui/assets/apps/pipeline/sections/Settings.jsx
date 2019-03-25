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

import { updateContract, addContract, selectSection } from '../redux'
import { isEmpty } from '../../utils'
import { deriveEntityTypes, deriveMappingRules } from '../../utils/avro-utils'

import { Modal } from '../../components'
import ContractPublishButton from '../components/ContractPublishButton'
import SubmissionCard from '../components/SubmissionCard'

import {
  CONTRACT_SECTION_MAPPING
} from '../../utils/constants'

export class IdentityMapping extends Component {
  constructor (props) {
    super(props)

    this.state = {
      entityTypeName: props.inputSchema.name || ''
    }
  }

  render () {
    return (
      <React.Fragment>
        {
          !this.props.contract.is_identity &&
          <div className='identity-mapping'>
            <div className='toggle-default'>
              <input
                type='checkbox'
                id='toggle'
                checked={this.props.isIdentity}
                onChange={(e) => this.props.onChange(e)}
              />
              <label
                for='toggle'
                className='title-medium'>
                <FormattedMessage
                  id='settings.identity.help-1'
                  defaultMessage='Create an identity contract'
                />
              </label>
            </div>
            <p>
              <FormattedMessage
                id='settings.identity.help-2'
                defaultMessage='An identity contract will produce entities
                that are identical with the input. If you choose this setting.
                Aether will generate an Entity Type and Mapping for you.'
              />
            </p>
            <p>
              <FormattedMessage
                id='settings.identity.help-3'
                defaultMessage="This can be useful in situations where you
                want to make use of Aether's functionality without transforming
                  the data Alternatively, you can use the generate Entity Type
                  and Mapping as a starting point for a more complex contract."
              />
            </p>
            { this.props.isIdentity && <div className='form-group'>
              <label className='form-label'>
                <FormattedMessage
                  id='settings.contract.identity.name'
                  defaultMessage='Entity Type name'
                />
              </label>
              <input
                type='text'
                required
                name='name'
                className='input-d contract-name'
                value={this.state.entityTypeName}
                onChange={(e) => { this.setState({ entityTypeName: e.target.value }) }}
              />
            </div>}
          </div>
        }

        {
          this.props.contract.is_identity &&
          <div className='identity-mapping'>
            <h5>
              <FormattedMessage
                id='settings.identity.checked.help-1'
                defaultMessage='This is an identity contract'
              />
            </h5>
            <p>
              <FormattedMessage
                id='settings.identity.checked.help-2'
                defaultMessage='All Entity Types and Mappings were generated automatically from the input'
              />
            </p>
          </div>
        }

        { this.props.showModal && this.renderModal() }
      </React.Fragment>
    )
  }

  generateIdentityMapping () {
    const schema = this.props.inputSchema
    const mappingRules = deriveMappingRules(schema, this.state.entityTypeName)
    const entityTypes = deriveEntityTypes(schema, this.state.entityTypeName)

    const updatedContract = {
      ...this.props.contract,
      mapping_rules: mappingRules,
      entity_types: entityTypes,
      name: this.props.contractName,
      is_identity: true
    }

    this.props.onSave(updatedContract)
    this.props.onModalToggle(false)
    this.props.selectSection(CONTRACT_SECTION_MAPPING)
  }

  onChange (e) {
    this.setState({
      isIdentity: e.target.checked
    })
    this.props.onChange(e)
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

        <button className='btn btn-w' onClick={() => { this.props.onModalToggle(false) }}>
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
      contractName: props.contract.name,
      isIdentity: false,
      showIdentityModal: false
    }
  }

  componentDidUpdate (prevProps) {
    if (prevProps.contract.name !== this.props.contract.name) {
      this.setState({ contractName: this.props.contract.name })
    }
  }

  onSave (contract) {
    if (this.state.isIdentity) {
      this.setState({
        showIdentityModal: true
      })
    } else {
      this.performSave({ ...contract, name: this.state.contractName })
    }
  }

  performSave (contract) {
    if (this.props.isNew) {
      this.props.addContract(contract)
      this.props.onSave(this.state.isIdentity ? CONTRACT_SECTION_MAPPING : null)
    } else {
      this.props.updateContract(contract)
      this.props.onClose()
    }
  }

  render () {
    const { contract } = this.props
    const showIdentityOption = (!contract.is_read_only && !isEmpty(this.props.inputSchema))

    return (
      <div className='pipeline-settings'>
        <div className='contract-form'>
          <div className='form-group'>
            <label className='form-label'>
              <FormattedMessage
                id='settings.contract.name'
                defaultMessage='Contract name'
              />
            </label>
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

          { showIdentityOption && <IdentityMapping {...this.props}
            onChange={(e) => this.setState({ isIdentity: e.target.checked })}
            isIdentity={this.state.isIdentity}
            showModal={this.state.showIdentityModal}
            onModalToggle={(e) => this.setState({ showIdentityModal: e })}
            contractName={this.state.contractName}
            onSave={this.performSave.bind(this)} /> }

          <div className='settings-section'>
            <div>
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

          <button
            onClick={() => this.props.onClose()}
            type='button'
            className='btn btn-d btn-big'>
            <span className='details-title'>
              <FormattedMessage
                id='settings.button.cancel'
                defaultMessage='Cancel'
              />
            </span>
          </button>
          { !contract.is_read_only &&
            <button
              className='btn btn-d btn-primary btn-big ml-4'
              onClick={this.onSave.bind(this, contract)}>
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
const mapDispatchToProps = { updateContract, addContract, selectSection }

export default connect(mapStateToProps, mapDispatchToProps)(Settings)
