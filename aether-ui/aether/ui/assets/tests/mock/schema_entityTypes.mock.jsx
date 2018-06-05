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

const entityTypes = [
  {
    'type': 'record',
    'name': 'Person',
    'fields': [
      {
        'name': 'hatId',
        'type': 'string'
      },
      {
        'name': 'firstName',
        'type': 'string'
      },
      {
        'name': 'lastName',
        'type': 'string'
      },
      {
        'name': 'age',
        'type': 'int'
      },
      {
        'name': 'gender',
        'type': {
          'type': 'enum',
          'name': 'Gender',
          'symbols': [ 'MALE', 'FEMALE' ]
        }
      }
    ]
  },
  {
    'type': 'record',
    'name': 'Screening',
    'fields': [
      {
        'name': 'hatId',
        'type': 'string'
      },
      {
        'name': 'screening',
        'type': {
          'type': 'enum',
          'name': 'ScreeningType',
          'symbols': [ 'maect', 'catt', 'pg', 'ctcwoo', 'ge', 'pl' ]
        }
      },
      {
        'name': 'location',
        'type': {
          'type': 'record',
          'name': 'GeoLocation',
          'fields': [
            {
              'name': 'latitude',
              'type': 'float'
            },
            {
              'name': 'longitude',
              'type': 'float'
            }
          ]
        }
      },
      {
        'name': 'result',
        'type': {
          'type': 'enum',
          'name': 'Result',
          'symbols': [ 'positive', 'negative' ]
        }
      }
    ]
  }
]

export default entityTypes
