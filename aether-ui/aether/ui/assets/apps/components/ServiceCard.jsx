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

import React, { Fragment } from 'react'

const sampleAbout = `
  Lorem ipsum dolor sit amet, 
  consectetur adipiscing elit, 
  sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
  `

const getStyle = (color) => ({ fontSize: 25, margin: 5, color: `${color}` })

const withSymbols = (service, color) => (
  <span>
    <i style={getStyle(color)}>&lt;</i>
      {service}
    <i style={getStyle(color)}>&gt;</i>
  </span>
)

const getIcon = (service) => {
  switch (service) {
    case 'gather':
      return <b>{service}</b>
    case 'aether':
      return <span><b>ae</b>ther</span>
    case 'kernel':
      return withSymbols('Kernel', '#50aef3')
    case 'odk':
      return withSymbols('ODK', '#d25b69')
    case 'kibana':
      return 'Kibana'
    default:
      return service
  }
}

export default ({ name, link, about = sampleAbout }) => {
  const showIcon = !['kernel', 'odk'].includes(name)
  
  return name ? (
    <Fragment>
      <a href={link}>
        <div className={`${name}-card title-large`}>
          {showIcon && <i className='fa fa-link mr-2' />}
          {getIcon(name)}
        </div>
      </a>
      <p className='service-about small'>{about}</p>
    </Fragment>
  ) : <div className={`-card`} />
}
