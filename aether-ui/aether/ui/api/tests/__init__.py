PIPELINE_EXAMPLE = {
  'name': 'Pipeline Example',
  'schema': {
    'name': 'hat',
    'type': 'record',
    'fields': [
      {
        'name': 'person',
        'type': {
          'name': 'person',
          'type': 'record',
          'fields': [
            {
              'name': 'forename',
              'type': 'string'
            },
            {
              'name': 'surname',
              'type': 'string'
            },
            {
              'name': 'age',
              'type': {
                'name': 'age',
                'type': 'record',
                'fields': [
                  {
                    'name': 'years',
                    'type': 'string'
                  }
                ],
                'namespace': 'age'
              }
            }
          ]
        }
      },
      {
        'name': 'participant',
        'type': {
          'name': 'participant',
          'type': 'record',
          'fields': [
            {
              'name': 'memberType',
              'type': 'string'
            },
            {
              'name': 'screenings',
              'type': {
                'name': 'screenings',
                'type': 'record',
                'fields': [
                  {
                    'name': 'maect',
                    'type': {
                      'name': 'maect',
                      'type': 'record',
                      'fields': [
                        {
                          'name': 'sessionType',
                          'type': 'string'
                        },
                        {
                          'name': 'group',
                          'type': 'string'
                        },
                        {
                          'name': 'result',
                          'type': 'string'
                        }
                      ],
                      'namespace': 'maect.screenings'
                    }
                  }
                ],
                'namespace': 'screenings'
              }
            },
            {
              'name': 'screeningLocation',
              'type': {
                'name': 'screeningLocation',
                'type': 'record',
                'fields': [
                  {
                    'name': 'zone',
                    'type': 'string'
                  },
                  {
                    'name': 'area',
                    'type': 'string'
                  },
                  {
                    'name': 'village',
                    'type': 'string'
                  }
                ],
                'namespace': 'screeningLocation'
              }
            },
            {
              'name': 'hatId',
              'type': 'string'
            },
            {
              'name': 'version',
              'type': 'int'
            },
            {
              'name': 'geoLocation',
              'type': {
                'name': 'geoLocation',
                'type': 'record',
                'fields': [
                  {
                    'name': 'accuracy',
                    'type': 'int'
                  },
                  {
                    'name': 'latitude',
                    'type': 'double'
                  },
                  {
                    'name': 'longitude',
                    'type': 'double'
                  },
                  {
                    'name': 'timestamp',
                    'type': 'long'
                  }
                ],
                'namespace': 'geoLocation'
              }
            }
          ],
          'namespace': ''
        }
      },
      {
        'name': 'type',
        'type': 'string'
      },
      {
        'name': 'dateCreated',
        'type': 'string'
      },
      {
        'name': 'dateModified',
        'type': 'string'
      },
      {
        'name': '_id',
        'type': 'string'
      },
      {
        'name': '_rev',
        'type': 'string'
      }
    ],
    'namespace': 'org.ehealthafrica'
  },
  'input': {
    '_id': 'participant-jhfnjdt1982m',
    '_rev': '2-2a896000d68883bb22ac3aa80dff71a6',
    'type': 'participant',
    'person': {
      'forename': 'a',
      'surname': 'b',
      'age': {
        'years': '43'
      }
    }
  },
  'entity_types': [
    {
      'name': 'PersonY',
      'type': 'record',
      'fields': [
        {
          'name': 'id',
          'type': 'string'
        },
        {
          'name': 'firstName',
          'type': 'string'
        }
      ]
    },
    {
      'name': 'Screening',
      'type': 'record',
      'fields': [
        {
          'name': 'id',
          'type': 'string'
        },
        {
          'name': 'screening',
          'type': {
            'name': 'ScreeningType',
            'type': 'enum',
            'symbols': [
              'maect',
              'catt',
              'pg',
              'ctcwoo',
              'ge',
              'pl'
            ]
          }
        },
        {
          'name': 'location',
          'type': {
            'name': 'GeoLocation',
            'type': 'record',
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
            'name': 'Result',
            'type': 'enum',
            'symbols': [
              'positive',
              'negative'
            ]
          }
        }
      ]
    }
  ],
  'mapping': [
    {
      'source': '#!uuid',
      'destination': 'PersonY.id'
    },
    {
      'source': 'person.forename',
      'destination': 'PersonY.firstName'
    }
  ],
  'mapping_errors': [],
  'output': [
    {
      'id': '0d8aebf3-50d0-4e77-a5ee-1045ffa5f29f',
      'firstName': 'Sejflsd Dljljkf'
    }
  ]
}

PIPELINE_EXAMPLE_1 = {
  'name': 'Pipeline Example 1',
  'schema': {
    'name': 'hat',
    'type': 'record',
    'fields': [
      {
        'name': 'person',
        'type': {
          'name': 'person',
          'type': 'record',
          'fields': [
            {
              'name': 'forename',
              'type': 'string'
            },
            {
              'name': 'surname',
              'type': 'string'
            }
          ]
        }
      }
    ]
  },
  'input': {
    'person': {
      'age': 54,
      'surname': 'Lfdjk',
      'forename': 'Sejflsd Dljljkf'
    }
  },
  'entity_types': [
    {
      'name': 'Person',
      'type': 'record',
      'fields': [
        {
          'name': 'id',
          'type': 'string'
        },
        {
          'name': 'firstName',
          'type': 'string'
        }
      ]
    },
    {
      'name': 'Screening',
      'type': 'record',
      'fields': [
        {
          'name': 'id',
          'type': 'string'
        }
      ]
    },
    {
      'name': 'PersonX',
      'type': 'record',
      'fields': [
        {
          'name': 'id',
          'type': 'string'
        },
        {
          'name': 'firstName',
          'type': 'string'
        }
      ]
    }
  ],
  'mapping': [
    {
      'source': '#!uuid',
      'destination': 'Person.id'
    },
    {
      'source': 'person.forename',
      'destination': 'Person.firstName'
    },
    {
      'source': '#!uuid',
      'destination': 'Screening.id'
    }
  ],
  'output': [
    {
      'id': '0d8aebf3-50d0-4e77-a5ee-1045ffa5f29f',
      'firstName': 'Sejflsd Dljljkf'
    },
    {
      'id': '5c40d8bb-7d3e-48cb-a008-7a55b97950de'
    }
  ],
  'kernel_refs': {
    'project': '12345',
    'schema': {
      'Person': '1234'
    },
    'projectSchema': {
      'Person': '1234'
    },
    'mapping': '1234'
  }
}


PIPELINE_EXAMPLE_WITH_MAPPING_ERRORS = {
  'name': 'Pipeline Example With Mapping Errors',
  'schema': {
    'name': 'hat',
    'type': 'record',
    'fields': [
      {
        'name': 'person',
        'type': {
          'name': 'person',
          'type': 'record',
          'fields': [
            {
              'name': 'forename',
              'type': 'string'
            }
          ]
        }
      }
    ]
  },
  'entity_types': [
    {
      'name': 'PersonZ',
      'type': 'record',
      'fields': [
        {
          'name': 'id',
          'type': 'string'
        },
        {
          'name': 'firstName',
          'type': 'string'
        }
      ]
    }
  ],
  'mapping': [
    {
      'source': '#!uuid',
      'destination': 'Person.id'
    },
    {
      'source': 'person.forename',
      'destination': 'Person.firstName'
    }
  ],
  'output': [
    {
      'id': '0d8aebf3-50d0-4e77-a5ee-1045ffa5f29f',
      'firstName': 'Sejflsd Dljljkf'
    }
  ],
  'input': {
    'person': {
      'forename': 'Sejflsd Dljljkf'
    }
  }
}
