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
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

import { selectPipeline } from '../redux'

class ContractAddButton extends Component {
  render () {
    const handleCreateNewContract = () => {
      const { id } = this.props.pipeline

      this.props.selectPipeline(id)
      this.props.history.push({
        pathname: `/${id}`,
        state: { isNewContract: true }
      })
    }

    return (
      <button
        type='button'
        className={this.props.className || 'btn btn-c'}
        onClick={handleCreateNewContract}
      >
        <span className='details-title'>
          <FormattedMessage
            id='contract.add.button'
            defaultMessage='Add contract'
          />
        </span>
      </button>
    )
  }
}

const mapStateToProps = () => ({})
const mapDispatchToProps = { selectPipeline }

export default connect(mapStateToProps, mapDispatchToProps)(ContractAddButton)
