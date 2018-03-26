PATH_DIR = '/code/aether/kernel/api/tests/files/'

SCHEMA_FILE_EMPTY = PATH_DIR + 'empty_schema.json'
SCHEMA_FILE_SAMPLE = PATH_DIR + 'sample_schema.json'
SCHEMA_FILE_ERROR = PATH_DIR + 'err_schema.json'

EXAMPLE_MAPPING = {
    'entities': {
        'Person': 1
    },
    'mapping': [
        ['#!uuid', 'Person.id'],
        ['data.village', 'Person.villageID'],
        ['data.people[*].name', 'Person.name'],
        ['data.people[*].dob', 'Person.dob']
    ]
}

EXAMPLE_SCHEMA = {
    'extends': 'http://ehealthafrica.org/#CouchDoc',
    'type': 'record',
    'name': 'Person',
    'fields': [
        {
            'jsonldPredicate': '@id',
            'type': 'string',
            'name': 'id',
            'inherited_from': 'http://ehealthafrica.org/#CouchDoc'
        },
        {
            'type': [
                'null',
                'string',
                ],
            'name': '_rev',
            'inherited_from': 'http://ehealthafrica.org/#CouchDoc'
        },
        {
            'type': [
                'null',
                'string',
                {
                    'type': 'array',
                    'items': 'string'
                }
            ],
            'name': 'name'
        },
        {
            'type': 'string',
            'name': 'dob'
        },
        {
            'jsonldPredicate': {
                '_type': '@id',
                '_id': 'http://ehealthafrica.org/#Village'
            },
            'type': 'string',
            'name': 'villageID'
        }
    ]
}

EXAMPLE_SOURCE_DATA = {
    'data': {
        'village': 'somevillageID',
        'people': [
            {
                'name': 'PersonA',
                'dob': '2000-01-01'
            },
            {
                'name': 'PersonB',
                'dob': '2001-01-01'
            },
            {
                'name': 'PersonC',
                'dob': '2002-01-01'
            }
        ]
    }
}

EXAMPLE_SOURCE_DATA_ENTITY = {
    'villageID': 'somevillageID',
    'name': 'Person-Valid',
    'dob': '2000-01-01',
    'id': 'somerandomID'
}

EXAMPLE_REQUIREMENTS = {
    'Person': {
        'id': ['#!uuid'],
        '_rev': [],
        'name': ['data.people[*].name'],
        'dob': ['data.people[*].dob'],
        'villageID': ['data.village']
    }
}

EXAMPLE_ENTITY = {
    'Person': [
        {
            'id': '1d119b5d-ca71-4f03-a061-1481e1a694ea',
            'name': 'PersonA',
            'dob': '2000-01-01',
            'villageID': 'somevillageID'
        },
        {
            'id': '5474b768-92d9-431f-bf90-3c6db1788109',
            'name': 'PersonB',
            'dob': '2001-01-01',
            'villageID': 'somevillageID'
        },
        {
            'id': '64d30f72-c15e-4476-9522-d26cb036c73b',
            'name': 'PersonC',
            'dob': '2002-01-01',
            'villageID': 'somevillageID'
        }
    ]
}

EXAMPLE_ENTITY_DEFINITION = {'Person': ['id', '_rev', 'name', 'dob', 'villageID']}

EXAMPLE_FIELD_MAPPINGS = [
    ['#!uuid', 'Person.id'],
    ['data.village', 'Person.villageID'],
    ['data.people[*].name', 'Person.name'],
    ['data.people[*].dob', 'Person.dob']]

SAMPLE_LOCATION_SCHEMA_DEFINITION = {
    'name': 'Location',
    'type': 'record',
    'fields': [
        {
            'name': 'id',
            'type': 'string',
            'jsonldPredicate': '@id'
        },
        {
            'name': 'revision',
            'type': [
                'null',
                'string'
            ]
        },
        {
            'name': 'lat',
            'type': 'float'
        },
        {
            'name': 'lng',
            'type': 'float'
        }
    ]
}

SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION = {
    'name': 'Household',
    'type': 'record',
    'fields': [
        {
            'name': 'id',
            'type': 'string',
            'jsonldPredicate': '@id'
        },
        {
            'name': 'revision',
            'type': [
                'null',
                'string'
            ]
        },
        {
            'name': 'locationID',
            'type': [
                'null',
                'string'
            ],
            'jsonldPredicate': {
                '_id': 'http://ehealthafrica.org/#Location',
                '_type': '@id'
            }
        }
    ]
}

SAMPLE_LOCATION_DATA = {
    'lat': 6.951801,
    'lng': -2.7539059999999997,
    'id': '00f3f1ae-abab-448b-b12f-f9c1839465ab'
}

SAMPLE_HOUSEHOLD_DATA = {
    'locationID': '00f3f1ae-abab-448b-b12f-f9c1839465ab'
}

EXAMPLE_GAMETOKEN_SCHEMA = {
    'fields': [
      {
        'jsonldPredicate': '@id',
        'type': 'string',
        'name': 'id',
        'inherited_from': 'http://game.eha.org/BaseModel'
      },
      {
        'type': 'string',
        'name': 'rev',
        'inherited_from': 'http://game.eha.org/BaseModel'
      },
      {
        'doc': 'A description of the thing.',
        'jsonldPredicate': 'http://game.eha.org/description',
        'type': [
          'null',
          'string',
          {
            'items': 'string',
            'type': 'array'
          }
        ],
        'name': 'description'
      },
      {
        'doc': 'A token value, true for positive, false for negative',
        'jsonldPredicate': 'http://game.eha.org/tokenValue',
        'type': [
          'null',
          'boolean'
        ],
        'name': 'tokenValue'
      },
      {
        'doc': 'The time something was created',
        'jsonldPredicate': 'http://game.eha.org/generationTime',
        'type': [
          'null',
          'string',
          {
            'items': 'string',
            'type': 'array'
          }
        ],
        'name': 'generationTime'
      },
      {
        'doc': 'A hash to maintain the integrity of generated tokens.',
        'jsonldPredicate': 'http://game.eha.org/securityHash',
        'type': [
          'null',
          'string',
          {
            'items': 'string',
            'type': 'array'
          }
        ],
        'name': 'securityHash'
      },
      {
        'doc': 'A common name for this entity.',
        'jsonldPredicate': 'http://game.eha.org/name',
        'type': [
          'null',
          'string',
          {
            'items': 'string',
            'type': 'array'
          }
        ],
        'name': 'name'
      }
    ],
    'type': 'record',
    'name': 'http://game.eha.org/GameToken',
    'extends': 'http://game.eha.org/BaseModel'
  }

EXAMPLE_VALID_PAYLOAD = {
    'id': 'bdc639fe-b142-4587-b2e9-4dc1a51f9a5d',
    'rev': 'some1srevision'
}

EXAMPLE_INVALID_PAYLOAD = {
    'id': 'bdc639fe-b142-4587-b2e9-4dc1a51f9a5c',
    'rev': 'some1srevision',
    'tokenValue': 'shouldhavebeenaboolean!'
}
