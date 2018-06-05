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

const inputSchema = {
  'type': 'record',
  'name': 'hat',
  'namespace': 'org.ehealthafrica',
  'fields': [{
    'name': 'person',
    'type': {
      'type': 'record',
      'name': 'person',
      'namespace': '',
      'fields': [{
        'name': 'forename',
        'type': 'string'
      }, {
        'name': 'surname',
        'type': 'string'
      }, {
        'name': 'age',
        'type': {
          'type': 'record',
          'name': 'person',
          'namespace': 'age',
          'fields': [{
            'name': 'years',
            'type': 'string'
          }]
        }
      }, {
        'name': 'gender',
        'type': 'string'
      }, {
        'name': 'mothersForename',
        'type': 'string'
      }, {
        'name': 'location',
        'type': {
          'type': 'record',
          'name': 'person',
          'namespace': 'location',
          'fields': [{
            'name': 'zone',
            'type': 'string'
          }, {
            'name': 'area',
            'type': 'string'
          }, {
            'name': 'village',
            'type': 'string'
          }]
        }
      }, {
        'name': 'birthYear',
        'type': 'int'
      }]
    }
  }, {
    'name': 'participant',
    'type': {
      'type': 'record',
      'name': 'participant',
      'namespace': '',
      'fields': [{
        'name': 'memberType',
        'type': 'string'
      }, {
        'name': 'screenings',
        'type': {
          'type': 'record',
          'name': 'participant',
          'namespace': 'screenings',
          'fields': [{
            'name': 'maect',
            'type': {
              'type': 'record',
              'name': 'participant',
              'namespace': 'maect.screenings',
              'fields': [{
                'name': 'sessionType',
                'type': 'string'
              }, {
                'name': 'group',
                'type': 'string'
              }, {
                'name': 'result',
                'type': 'string'
              }]
            }
          }]
        }
      }, {
        'name': 'screeningLocation',
        'type': {
          'type': 'record',
          'name': 'participant',
          'namespace': 'screeningLocation',
          'fields': [{
            'name': 'zone',
            'type': 'string'
          }, {
            'name': 'area',
            'type': 'string'
          }, {
            'name': 'village',
            'type': 'string'
          }]
        }
      }, {
        'name': 'hatId',
        'type': 'string'
      }, {
        'name': 'version',
        'type': 'int'
      }, {
        'name': 'geoLocation',
        'type': {
          'type': 'record',
          'name': 'participant',
          'namespace': 'geoLocation',
          'fields': [{
            'name': 'accuracy',
            'type': 'int'
          }, {
            'name': 'latitude',
            'type': 'double'
          }, {
            'name': 'longitude',
            'type': 'double'
          }, {
            'name': 'timestamp',
            'type': 'long'
          }]
        }
      }]
    }
  }, {
    'name': 'type',
    'type': 'string'
  }, {
    'name': 'dateCreated',
    'type': 'string'
  }, {
    'name': 'dateModified',
    'type': 'string'
  }, {
    'name': '_id',
    'type': 'string'
  }, {
    'name': '_rev',
    'type': 'string'
  }]
}

export default inputSchema
