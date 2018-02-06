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
                'string'
            ],
            'name': '_rev',
            'inherited_from': 'http://ehealthafrica.org/#CouchDoc'
        },
        {
            'type': 'string',
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
