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

import React from 'react'
import { FormattedMessage } from 'react-intl'
import { NavBar, ServiceCard } from '../components'
import { capitalize, getServices } from '../utils'

export default ({ tenant = 'doug' }) => (
  <div className='landing-page'>
    <NavBar />

    <div className="content">
      <div className='tenant-name'>
        <FormattedMessage
          id='landing.page.tenant.name'
          defaultMessage={tenant ? capitalize(tenant) : ' '}
        />
      </div>

      <div className='title-medium'>
        <FormattedMessage
          id='landing.page.tenant.services'
          defaultMessage='Services'
        />
      </div>

      <div className="services">
        {
          getServices(tenant).map((service, index) => (
              <div key={`${service.name}${index}`} className="service">
                <ServiceCard {...service} />
              </div>
            )
          )
        }
      </div>
    </div>
  </div>
)
