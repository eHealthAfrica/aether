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
import { Modal } from '../../components'
import { connect } from 'react-redux'
import { FormattedMessage, injectIntl } from 'react-intl'

class DeleteStatus extends Component {
  constructor (props) {
    super(props)
    this.state = {
    }
  }

  componentDidUpdate () {
    if (
      this.props.error ||
      (this.props.deleteStatus && this.props.deleteStatus.not_published)
    ) {
      this.props.toggle()
    }
  }

  render () {
    if (!this.props.showModal) {
      return null
    }

    const header = this.props.header
    const close = () => { this.props.toggle() }

    const buttons = (
      <div className='modal-actions'>
        {
          this.props.deleteStatus &&
            <button
              className='btn btn-primary btn-w'
              onClick={close}
            >
              <FormattedMessage
                id='delete.progress.modal.ok'
                defaultMessage='Close'
              />
            </button>
        }
      </div>
    )

    return (
      <Modal header={header} buttons={buttons}>
        {
          !this.props.deleteStatus && (
            <label className='title-medium mt-4'>
              <FormattedMessage
                id='delete.modal.status.head-1'
                defaultMessage='Deleting kernel artefacts...'
              />
              <i className='ml-5 fa fa-cog fa-spin' />
            </label>
          )
        }

        {
          this.props.deleteOptions.entities &&
          this.props.deleteStatus &&
          Object.prototype.hasOwnProperty.call(this.props.deleteStatus, 'entities') &&
            <div>
              <label className='form-label'>
                <span className='badge badge-b'>
                  {this.props.deleteStatus.entities.total}
                </span>
                <FormattedMessage
                  id='delete.modal.entities.status'
                  defaultMessage='Entities deleted'
                />
              </label>
              <div className='ml-5'>
                {
                  this.props.deleteStatus.entities.schemas.map(schema => (
                    <div key={schema.name}>
                      <i className='fa fa-check mr-2' />
                      <label>
                        {schema.name} : {schema.count}
                      </label>
                    </div>
                  ))
                }
              </div>
            </div>
        }

        {
          this.props.deleteOptions.schemas && this.props.deleteStatus &&
          this.props.deleteStatus.schemas && (
            <div>
              <label className='form-label mt-4'>
                <span className='badge badge-b'>
                  {Object.keys(this.props.deleteStatus.schemas).length}
                </span>
                <FormattedMessage
                  id='delete.modal.entity.types.status'
                  defaultMessage='Entity types deleted'
                />
              </label>
              <div className='ml-5'>
                {
                  Object.keys(this.props.deleteStatus.schemas).map(schema => (
                    <div key={schema}>
                      <i className='fa fa-check mr-2' />
                      <label>
                        {schema} :
                        {
                          this.props.deleteStatus.schemas[schema].is_deleted
                            ? (
                              <FormattedMessage
                                id='delete.modal.entity.types.status.deleted'
                                defaultMessage='Deleted'
                              />
                            )
                            : (
                              <FormattedMessage
                                id='delete.modal.entity.types.status.not.deleted'
                                defaultMessage='Not deleted, used by other mappings'
                              />
                            )
                        }
                      </label>
                    </div>
                  ))
                }
              </div>

              {
                Object.keys(this.props.deleteStatus.schemas).length === 0 &&
                  <label>
                    <FormattedMessage
                      id='delete.modal.entity.types.empty'
                      defaultMessage='No entity types to delete'
                    />
                  </label>
              }
            </div>
          )
        }

        {
          this.props.deleteOptions.submissions &&
          this.props.deleteStatus &&
          Object.prototype.hasOwnProperty.call(this.props.deleteStatus, 'submissions') &&
            <div>
              <label className='form-label mt-4'>
                <span className='badge badge-b'>{this.props.deleteStatus.submissions}</span>
                <FormattedMessage
                  id='delete.modal.sumbissions.status'
                  defaultMessage='Submissions deleted'
                />
              </label>
            </div>
        }
      </Modal>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  error: pipelines.error,
  deleteStatus: pipelines.deleteStatus
})

export default connect(mapStateToProps, {})(injectIntl(DeleteStatus))
