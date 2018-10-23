# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

EXAMPLE_MAPPING = {
    'entities': {
        'Person': '1',
    },
    'mapping': [
        ['#!uuid', 'Person.id'],
        ['data.village', 'Person.villageID'],
        ['data.people[*].name', 'Person.name'],
        ['data.people[*].dob', 'Person.dob'],
    ],
}

EXAMPLE_SCHEMA = {
    'extends': 'http://ehealthafrica.org/#CouchDoc',
    'type': 'record',
    'name': 'Person',
    'aetherBaseSchema': True,
    'fields': [
        {
            'jsonldPredicate': '@id',
            'type': 'string',
            'name': 'id',
            'doc': 'ID',
            'inherited_from': 'http://ehealthafrica.org/#CouchDoc',
        },
        {
            'type': [
                'null',
                'string',
            ],
            'name': '_rev',
            'doc': 'REVISION',
            'inherited_from': 'http://ehealthafrica.org/#CouchDoc',
        },
        {
            'type': [
                'null',
                'string',
                {
                    'type': 'array',
                    'items': 'string',
                }
            ],
            'name': 'name',
            'doc': 'NAME',
        },
        {
            'type': 'string',
            'name': 'dob',
        },
        {
            'jsonldPredicate': {
                '_type': '@id',
                '_id': 'http://ehealthafrica.org/#Village',
            },
            'type': 'string',
            'name': 'villageID',
            'doc': 'VILLAGE',
        },
    ],
}

EXAMPLE_SOURCE_DATA = {
    'data': {
        'village': 'somevillageID',
        'people': [
            {
                'name': 'PersonA',
                'dob': '2000-01-01',
            },
            {
                'name': 'PersonB',
                'dob': '2001-01-01',
            },
            {
                'name': ['FirstC', 'MiddleC', 'LastC'],
                'dob': '2002-01-01',
            },
        ],
    },
}

EXAMPLE_NESTED_SOURCE_DATA = {
    'data': {
        'village': 'somevillageID',
        'houses': [
            {
                'num': 0,
                'people': [
                    {
                        'name': 'PersonA',
                        'dob': '2000-01-01',
                    },
                    {
                        'name': 'PersonB',
                        'dob': '2001-01-01',
                    },
                    {
                        'name': ['FirstC', 'MiddleC', 'LastC'],
                        'dob': '2002-01-01',
                    },
                ],
            },
            {
                'num': 1,
                'people': [
                    {
                        'name': 'PersonD',
                        'dob': '2000-01-01',
                    },
                    {
                        'name': 'PersonE',
                        'dob': '2001-01-01',
                    },
                    {
                        'name': 'PersonF',
                        'dob': '2002-01-01',
                    },
                ],
            },
        ],
    },
}

EXAMPLE_PARTIAL_WILDCARDS = {
    'households': [
        {
            'address': '74 Whyioughta St.',
            'name1': 'Larry',
            'number1': 1,
            'name2': 'Curly',
            'number2': 2
        },
        {
            'address': '1600 Ipoke Ave',
            'name1': 'Moe',
            'number1': 3
        }
    ]
}

EXAMPLE_SOURCE_DATA_ENTITY = {
    'villageID': 'somevillageID',
    'name': 'Person-Valid',
    'dob': '2000-01-01',
    'id': 'somerandomID',
}

EXAMPLE_REQUIREMENTS = {
    'Person': {
        'id': ['#!uuid'],
        '_rev': [],
        'name': ['data.people[*].name'],
        'dob': ['data.people[*].dob'],
        'villageID': ['data.village'],
    },
}

EXAMPLE_ENTITY = {
    'Person': [
        {
            'id': '1d119b5d-ca71-4f03-a061-1481e1a694ea',
            'name': 'PersonA',
            'dob': '2000-01-01',
            'villageID': 'somevillageID',
        },
        {
            'id': '5474b768-92d9-431f-bf90-3c6db1788109',
            'name': 'PersonB',
            'dob': '2001-01-01',
            'villageID': 'somevillageID',
        },
        {
            'id': '64d30f72-c15e-4476-9522-d26cb036c73b',
            'name': ['FirstC', 'MiddleC', 'LastC'],
            'dob': '2002-01-01',
            'villageID': 'somevillageID',
        },
    ],
}

EXAMPLE_ENTITY_DEFINITION = {'Person': ['id', '_rev', 'name', 'dob', 'villageID']}

EXAMPLE_FIELD_MAPPINGS = [
    ['#!uuid', 'Person.id'],
    ['data.village', 'Person.villageID'],
    ['data.people[*].name', 'Person.name'],
    ['data.people[*].dob', 'Person.dob'],
]

SAMPLE_LOCATION_SCHEMA_DEFINITION = {
    'name': 'Location',
    'type': 'record',
    'fields': [
        {
            'name': 'id',
            'type': 'string',
            'jsonldPredicate': '@id',
        },
        {
            'name': 'revision',
            'type': [
                'null',
                'string',
            ],
        },
        {
            'name': 'lat',
            'type': 'float',
        },
        {
            'name': 'lng',
            'type': 'float',
        },
    ],
}

SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION = {
    'name': 'Household',
    'type': 'record',
    'fields': [
        {
            'name': 'id',
            'type': 'string',
            'jsonldPredicate': '@id',
        },
        {
            'name': 'revision',
            'type': [
                'null',
                'string',
            ],
        },
        {
            'name': 'locationID',
            'type': [
                'null',
                'string',
            ],
            'jsonldPredicate': {
                '_id': 'http://ehealthafrica.org/#Location',
                '_type': '@id',
            },
        },
    ],
}

SAMPLE_LOCATION_DATA = {
    'id': '00f3f1ae-abab-448b-b12f-f9c1839465ab',
    'lat': 6.951801,
    'lng': -2.7539059999999997,
}

SAMPLE_HOUSEHOLD_DATA = {
    'id': 'bdc639fe-b142-4587-b2e9-4dc1a51f9a5c',
    'locationID': '00f3f1ae-abab-448b-b12f-f9c1839465ab',
}
