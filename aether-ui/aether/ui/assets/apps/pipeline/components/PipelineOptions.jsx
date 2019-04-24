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
import onClickOutside from 'react-onclickoutside'

class PipelineOptions extends Component {
  constructor (props) {
    super(props)

    this.state = {
      show: false
    }
  } 

  handleClickOutside () {
    this.setState({
      show: false
    })
  }

  toggle () {
    this.setState({
      show: !this.state.show
    })
  }

  render () {
    return (
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <button
          type='button'
          className='btn btn-c'
          onClick={this.toggle.bind(this)}>
          <span className='details-title'>
            <i className='fas fa-ellipsis-h' />
          </span>
        </button>
        {
          this.state.show && <div
            style={{
              background: '#fff',
              padding: '10px',
              cornerRadius: '5px',
              color: '#000',
              position: 'absolute',
              zIndex: 3,
              minWidth: '190px',
              borderRadius: '5px',
              boxShadow: '2px 2px 5px 1px rgba(0,0,0,0.5)',
              marginTop: '2px'
            }}>
            <ul>
              <li onClick={() => this.props.rename() }>Rename Pipeline</li>
              <li onClick={() => this.props.delete() }>Delete Pipeline</li>
            </ul>
          </div>
        }
      </div>
    )
  }
}

export default onClickOutside(PipelineOptions)
