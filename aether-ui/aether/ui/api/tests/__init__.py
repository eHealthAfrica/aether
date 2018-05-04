PIPELINE_EXAMPLE = {
  'id': '26aba171-fac3-487c-a9aa-696b2f552ad7',
  'url': 'http://ui.aether.local:8004/api/ui/pipelines/26aba171-fac3-487c-a9aa-696b2f552ad7/',
  'created': '2018-05-02T14:00:33.582535Z',
  'modified': '2018-05-02T14:01:26.219304Z',
  'name': 'Pipeline Mock 1',
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
            },
            {
              'name': 'gender',
              'type': 'string'
            },
            {
              'name': 'mothersForename',
              'type': 'string'
            },
            {
              'name': 'location',
              'type': {
                'name': 'location',
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
                'namespace': 'location'
              }
            },
            {
              'doc': 'Type inferred from 1972',
              'name': 'birthYear',
              'type': 'int'
            }
          ],
          'namespace': ''
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
      'age': {
        'years': '43'
      },
      'gender': 'Male',
      'surname': 'Lfdjk',
      'forename': 'Sejflsd Dljljkf',
      'location': {
        'area': 'muluma',
        'zone': 'mosango',
        'village': 'kisala-lupa'
      },
      'birthYear': 1972,
      'mothersForename': 'Fokdsh'
    },
    'dateCreated': '2016-04-08T05:20:43.804Z',
    'participant': {
      'hatId': 'JHFNJDT1982M',
      'version': 3,
      'memberType': 'resident',
      'screenings': {
        'maect': {
          'group': '2016-04-08T05:17:24.338Z',
          'result': 'negative',
          'sessionType': 'doorToDoor'
        }
      },
      'geoLocation': {
        'accuracy': 3,
        'latitude': -4.7555159,
        'longitude': 18.0578531,
        'timestamp': 1460092843080
      },
      'screeningLocation': {
        'area': 'muluma',
        'zone': 'mosango',
        'village': 'kisala-lupa'
      }
    },
    'dateModified': '2016-04-08T06:53:31.706Z'
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
            'name': 'Gender',
            'type': 'enum',
            'symbols': [
              'MALE',
              'FEMALE'
            ]
          }
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
      'id': 'a469a7b3-fbd4-25c1-649d-73cf14d34945',
      'source': '#!uuid',
      'destination': 'Person.id'
    },
    {
      'id': '58082cd0-548e-59e1-9fc7-748bb7f764c6',
      'source': 'person.forename',
      'destination': 'Person.firstName'
    },
    {
      'id': '2dec3021-ddec-323a-1ef8-0f529f380087',
      'source': 'person.surname',
      'destination': 'Person.lastName'
    },
    {
      'id': '063d4763-85be-81f3-a036-dddb68eddff4',
      'source': 'person.age.years',
      'destination': 'Person.age'
    },
    {
      'id': '827dd4fa-4fb7-2780-9198-5d83af7a1893',
      'source': 'person.gender',
      'destination': 'Person.gender'
    },
    {
      'id': 'ea9e4bbf-3491-08f8-4cf0-2fa846306abb',
      'source': '#!uuid',
      'destination': 'Screening.id'
    },
    {
      'id': '57473e7c-aa45-dce5-fa70-cdaa0a93fdf8',
      'source': 'participant.screenings',
      'destination': 'Screening'
    },
    {
      'id': 'ea064db4-ecd6-956a-9192-09881b6f885c',
      'source': 'participant.geoLocation.latitude',
      'destination': 'Screening.location.latitude'
    },
    {
      'id': '60ccb09d-66bc-cce9-419e-a43437b387e2',
      'source': 'participant.screenings.maect.result',
      'destination': 'Screening.result'
    }
  ],
  'mapping_errors': [
    {
      'path': 'Screening.location.latitude',
      'error_message': 'No match for path'
    }
  ],
  'output': [
    {
      'id': '0d8aebf3-50d0-4e77-a5ee-1045ffa5f29f',
      'age': '43',
      'gender': 'Male',
      'lastName': 'Lfdjk',
      'firstName': 'Sejflsd Dljljkf'
    },
    {
      'id': '5c40d8bb-7d3e-48cb-a008-7a55b97950de',
      'result': 'negative'
    }
  ]
}

PIPELINE_EXAMPLE_1 = {
  'name': 'Pipeline Mock 2',
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
            },
            {
              'name': 'gender',
              'type': 'string'
            },
            {
              'name': 'mothersForename',
              'type': 'string'
            },
            {
              'name': 'location',
              'type': {
                'name': 'location',
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
                'namespace': 'location'
              }
            },
            {
              'doc': 'Type inferred from 1972',
              'name': 'birthYear',
              'type': 'int'
            }
          ],
          'namespace': ''
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
      'age': {
        'years': '43'
      },
      'gender': 'Male',
      'surname': 'Lfdjk',
      'forename': 'Sejflsd Dljljkf',
      'location': {
        'area': 'muluma',
        'zone': 'mosango',
        'village': 'kisala-lupa'
      },
      'birthYear': 1972,
      'mothersForename': 'Fokdsh'
    },
    'dateCreated': '2016-04-08T05:20:43.804Z',
    'participant': {
      'hatId': 'JHFNJDT1982M',
      'version': 3,
      'memberType': 'resident',
      'screenings': {
        'maect': {
          'group': '2016-04-08T05:17:24.338Z',
          'result': 'negative',
          'sessionType': 'doorToDoor'
        }
      },
      'geoLocation': {
        'accuracy': 3,
        'latitude': -4.7555159,
        'longitude': 18.0578531,
        'timestamp': 1460092843080
      },
      'screeningLocation': {
        'area': 'muluma',
        'zone': 'mosango',
        'village': 'kisala-lupa'
      }
    },
    'dateModified': '2016-04-08T06:53:31.706Z'
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
            'name': 'Gender',
            'type': 'enum',
            'symbols': [
              'MALE',
              'FEMALE'
            ]
          }
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
            'name': 'Gender',
            'type': 'enum',
            'symbols': [
              'MALE',
              'FEMALE'
            ]
          }
        }
      ]
    }
  ],
  'mapping': [
    {
      'id': 'a469a7b3-fbd4-25c1-649d-73cf14d34945',
      'source': '#!uuid',
      'destination': 'Person.id'
    },
    {
      'id': '58082cd0-548e-59e1-9fc7-748bb7f764c6',
      'source': 'person.forename',
      'destination': 'Person.firstName'
    },
    {
      'id': '2dec3021-ddec-323a-1ef8-0f529f380087',
      'source': 'person.surname',
      'destination': 'Person.lastName'
    },
    {
      'id': '063d4763-85be-81f3-a036-dddb68eddff4',
      'source': 'person.age.years',
      'destination': 'Person.age'
    },
    {
      'id': '827dd4fa-4fb7-2780-9198-5d83af7a1893',
      'source': 'person.gender',
      'destination': 'Person.gender'
    },
    {
      'id': 'ea9e4bbf-3491-08f8-4cf0-2fa846306abb',
      'source': '#!uuid',
      'destination': 'Screening.id'
    },
    {
      'id': '57473e7c-aa45-dce5-fa70-cdaa0a93fdf8',
      'source': 'participant.screenings',
      'destination': 'Screening'
    },
    {
      'id': 'ea064db4-ecd6-956a-9192-09881b6f885c',
      'source': 'participant.geoLocation.latitude',
      'destination': 'Screening.location.latitude'
    },
    {
      'id': '60ccb09d-66bc-cce9-419e-a43437b387e2',
      'source': 'participant.screenings.maect.result',
      'destination': 'Screening.result'
    }
  ],
  'mapping_errors': [
    {
      'path': 'Screening.location.latitude',
      'error_message': 'No match for path'
    }
  ],
  'output': [
    {
      'id': '0d8aebf3-50d0-4e77-a5ee-1045ffa5f29f',
      'age': '43',
      'gender': 'Male',
      'lastName': 'Lfdjk',
      'firstName': 'Sejflsd Dljljkf'
    },
    {
      'id': '5c40d8bb-7d3e-48cb-a008-7a55b97950de',
      'result': 'negative'
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
