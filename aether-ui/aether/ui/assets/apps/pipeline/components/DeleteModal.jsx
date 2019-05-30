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
import { FormattedMessage, FormattedHTMLMessage, injectIntl, defineMessages } from 'react-intl'
import { Modal } from '../../components'

const MESSAGES = defineMessages({
  delete: {
    id: 'modal.delete.text',
    defaultMessage: 'Delete {obj} <b>{objName}</b>'
  },
  submissions: {
    id: 'modal.delete.submissions.text',
    defaultMessage: 'Data <b>submitted to</b> this pipeline (Submissions)'
  },
  entities: {
    id: 'modal.delete.entities.text',
    defaultMessage: 'Data <b>created by</b> this {obj} (Entities)'
  },
  pipeline: {
    id: 'modal.delete.object.type.pipeline',
    defaultMessage: 'pipeline'
  },
  contract: {
    id: 'modal.delete.object.type.contract',
    defaultMessage: 'contract'
  }
})

class DeleteModal extends Component {
  constructor (props) {
    super(props)
    this.state = {
      schemas: false,
      entities: false,
      submissions: false
    }
  }

  render () {
    const { formatMessage } = this.props.intl
    const objType = formatMessage(MESSAGES[this.props.objectType || 'pipeline'])
    const header = (
      <span>
        <FormattedHTMLMessage
          {...
          { ...MESSAGES.delete,
            values: {
              obj: objType,
              objName: this.props.obj.name
            }
          }
          }
        />
      </span>
    )

    const buttons = (
      <div>
        <button
          data-qa='delete.modal.button.cancel'
          className='btn btn-w'
          onClick={this.props.onClose}>
          <FormattedMessage
            id='delete.modal.button.cancel'
            defaultMessage='Cancel'
          />
        </button>

        <button className='btn btn-w btn-primary' onClick={() => this.props.onDelete(this.state)}>
          <FormattedMessage
            id='delete.modal.button.delete'
            defaultMessage='Delete'
          />
        </button>
      </div>
    )

    return (
      <Modal header={header} buttons={buttons}>
        <label className='title-medium mt-4'>
          <FormattedMessage
            id='delete.modal.message-2'
            defaultMessage='Would you also like to delete any of the following?'
          />
        </label>
        {
          this.props.objectType === 'pipeline' &&
          <div className='check-default ml-4'>
            <input type='checkbox' id='check1' checked={this.state.submissions}
              onChange={(e) => {
                this.setState({
                  ...this.state, submissions: e.target.checked
                })
              }}
            />
            <label htmlFor='check1'>
              <FormattedHTMLMessage
                {...
                { ...MESSAGES.submissions }
                }
              />
            </label>
          </div>
        }
        <div className='check-default ml-4'>
          <input type='checkbox' id='check2' checked={this.state.schemas}
            onChange={(e) => {
              this.setState({
                ...this.state,
                schemas: e.target.checked,
                entities: e.target.checked
              })
            }}
          />
          <label htmlFor='check2'>
            <FormattedMessage
              id='delete.modal.all.entity-types-0'
              defaultMessage='Entity Types (Schemas)'
            />
          </label>
        </div>
        <div className='check-default ml-4 check-indent'>
          <input type='checkbox' id='check3' checked={this.state.entities}
            onChange={(e) => {
              if (!e.target.checked) {
                this.setState({
                  ...this.state,
                  entities: e.target.checked,
                  schemas: e.target.checked
                })
              } else {
                this.setState({
                  ...this.state, entities: e.target.checked
                })
              }
            }}
          />
          <label htmlFor='check3'>
            <FormattedHTMLMessage
              {...
              { ...MESSAGES.entities,
                values: {
                  obj: objType
                }
              }
              }
            />
          </label>
        </div>
      </Modal>
    )
  }
}

export default injectIntl(DeleteModal)
