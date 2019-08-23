# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

TENANT = 'test'
MAPPINGSET_ID = '41282431-50bb-4309-92bf-ef9359494dc6'
PAYLOAD = {
    'id': 'a5336669-605c-4a65-ab4c-c0318e28115b',
    'staff': {
        'nurse': 40,
        'doctor': 15
    },
    'patient': {
        'name': 'Nancy William',
        'patient_id': 'c55021d0-cc34-46ba-ac5b-4cd5bcbde3f9'
    },
    'opening_hour': '7AM working days',
    'facility_name': 'Primary Health Care Abuja'
}
MAPPINGSET = {
    'id': MAPPINGSET_ID,
    'name': 'Dummy',
    'schema': {
        'name': 'Dummy',
        'type': 'record',
        'fields': [
            {
                'name': 'id',
                'type': 'string'
            },
            {
                'name': 'facility_name',
                'type': 'string'
            },
            {
                'name': 'staff',
                'type': {
                    'name': 'Auto_1',
                    'type': 'record',
                    'fields': [
                        {
                            'name': 'doctor',
                            'type': 'int'
                        },
                        {
                            'name': 'nurse',
                            'type': 'int'
                        }
                    ]
                }
            },
            {
                'name': 'opening_hour',
                'type': 'string'
            },
            {
                'name': 'patient',
                'type': {
                    'name': 'Auto_2',
                    'type': 'record',
                    'fields': [
                        {
                            'name': 'patient_id',
                            'type': 'string'
                        },
                        {
                            'name': 'name',
                            'type': 'string'
                        }
                    ]
                }
            }
        ]
    },
    'input': PAYLOAD
}

MAPPINGS = [
    {
        'id': '0d4a9cc6-291c-4f9a-a409-1ba87cc93c57',
        'mappingset': MAPPINGSET_ID,
        'revision': '1',
        'name': 'passthrough',
        'definition': {
            'mapping': [
                [
                    '$.id',
                    'Pass.id'
                ],
                [
                    '$.facility_name',
                    'Pass.facility_name'
                ],
                [
                    '$.staff',
                    'Pass.staff'
                ],
                [
                    '$.opening_hour',
                    'Pass.opening_hour'
                ],
                [
                    '$.patient',
                    'Pass.patient'
                ]
            ],
            'entities': {
                'Pass': 'cc3e081a-e802-47eb-a5ea-f1c056737453'
            }
        },
        'is_active': True,
        'is_read_only': False,
        'schemadecorators': [
            'cc3e081a-e802-47eb-a5ea-f1c056737453'
        ]
    },
    {
        'id': '3ae8649f-2d5d-4703-82d3-94baaee4914e',
        'mappingset': MAPPINGSET_ID,
        'revision': '1',
        'name': 'crossthrough',
        'definition': {
            'mapping': [
                [
                    '#!uuid',
                    'Facility.id'
                ],
                [
                    '$.patient.patient_id',
                    'Patient.id'
                ],
                [
                    '$.patient.name',
                    'Patient.name'
                ],
                [
                    '$.facility_name',
                    'Facility.name'
                ],
                [
                    '$.staff.doctor + $.staff.nurse',
                    'Facility.staff'
                ]
            ],
            'entities': {
                'Patient': '134a750e-913b-458f-80a1-394c03a64ba5',
                'Facility': '92ac6021-cc1d-47fa-95a0-3e497125c538'
            }
        },
        'is_active': True,
        'is_read_only': False,
        'schemadecorators': [
            '134a750e-913b-458f-80a1-394c03a64ba5',
            '92ac6021-cc1d-47fa-95a0-3e497125c538'
        ]
    }
]

SCHEMA_DECORATORS = [
    {
        'id': 'cc3e081a-e802-47eb-a5ea-f1c056737453',
        'schema_definition': {
            'name': 'Pass',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                },
                {
                    'name': 'facility_name',
                    'type': [
                        'null',
                        'string'
                    ]
                },
                {
                    'name': 'staff',
                    'type': [
                        'null',
                        {
                            'name': 'Auto_1',
                            'type': 'record',
                            'fields': [
                                {
                                    'name': 'doctor',
                                    'type': 'int'
                                },
                                {
                                    'name': 'nurse',
                                    'type': 'int'
                                }
                            ]
                        }
                    ]
                },
                {
                    'name': 'opening_hour',
                    'type': [
                        'null',
                        'string'
                    ]
                },
                {
                    'name': 'patient',
                    'type': [
                        'null',
                        {
                            'name': 'Auto_2',
                            'type': 'record',
                            'fields': [
                                {
                                    'name': 'patient_id',
                                    'type': 'string'
                                },
                                {
                                    'name': 'name',
                                    'type': 'string'
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        'name': 'Pass',
        'schema': 'cc3e081a-e802-47eb-a5ea-f1c056737453'
    },
    {
        'id': '134a750e-913b-458f-80a1-394c03a64ba5',
        'schema_definition': {
            'name': 'Patient',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                },
                {
                    'name': 'name',
                    'type': [
                        'null',
                        'string'
                    ]
                }
            ]
        },
        'name': 'Patient',
        'schema': '134a750e-913b-458f-80a1-394c03a64ba5'
    },
    {
        'id': '92ac6021-cc1d-47fa-95a0-3e497125c538',
        'schema_definition': {
            'name': 'Facility',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                },
                {
                    'name': 'name',
                    'type': [
                        'null',
                        'string'
                    ]
                },
                {
                    'name': 'staff',
                    'type': [
                        'null',
                        'int'
                    ]
                }
            ]
        },
        'name': 'Facility',
        'schema': '92ac6021-cc1d-47fa-95a0-3e497125c538'
    }
]

SCHEMAS = [
    {
        'id': 'cc3e081a-e802-47eb-a5ea-f1c056737453',
        'revision': '1',
        'name': 'Pass',
        'definition': {
            'name': 'Pass',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                },
                {
                    'name': 'facility_name',
                    'type': [
                        'null',
                        'string'
                    ]
                },
                {
                    'name': 'staff',
                    'type': [
                        'null',
                        {
                            'name': 'Auto_1',
                            'type': 'record',
                            'fields': [
                                {
                                    'name': 'doctor',
                                    'type': 'int'
                                },
                                {
                                    'name': 'nurse',
                                    'type': 'int'
                                }
                            ]
                        }
                    ]
                },
                {
                    'name': 'opening_hour',
                    'type': [
                        'null',
                        'string'
                    ]
                },
                {
                    'name': 'patient',
                    'type': [
                        'null',
                        {
                            'name': 'Auto_2',
                            'type': 'record',
                            'fields': [
                                {
                                    'name': 'patient_id',
                                    'type': 'string'
                                },
                                {
                                    'name': 'name',
                                    'type': 'string'
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        'family': None
    },
    {
        'id': '134a750e-913b-458f-80a1-394c03a64ba5',
        'revision': '1',
        'name': 'Patient',
        'definition': {
            'name': 'Patient',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                },
                {
                    'name': 'name',
                    'type': [
                        'null',
                        'string'
                    ]
                }
            ]
        },
        'family': None
    },
    {
        'id': '92ac6021-cc1d-47fa-95a0-3e497125c538',
        'revision': '1',
        'name': 'Facility',
        'definition': {
            'name': 'Facility',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                },
                {
                    'name': 'name',
                    'type': [
                        'null',
                        'string'
                    ]
                },
                {
                    'name': 'staff',
                    'type': [
                        'null',
                        'int'
                    ]
                }
            ]
        },
        'family': None
    }
]
SUBMISSION = {
    'mappingset': MAPPINGSET_ID,
    'payload': PAYLOAD,
    'mappings': [
        '0d4a9cc6-291c-4f9a-a409-1ba87cc93c57',
        '3ae8649f-2d5d-4703-82d3-94baaee4914e'
    ]
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

NESTED_ARRAY_SCHEMA = {
    'fields': [
        {
            'name': 'id',
            'type': 'string'
        },
        {
            'name': 'geom',
            'namespace': 'Test',
            'type': {
                'fields': [
                    {
                        'name': 'coordinates',
                        'namespace': 'Test.geom',
                        'type': {
                            'items': 'float',
                            'type': 'array'
                        }
                    },
                    {
                        'name': 'type',
                        'namespace': 'Test.geom',
                        'type': 'string'
                    }
                ],
                'name': 'geom',
                'namespace': 'Test',
                'type': 'record'
            }
        }
    ],
    'name': 'Test',
    'namespace': 'org.eha.Test',
    'type': 'record'
}

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

EXAMPLE_MAPPING_EDGE = {
    'entities': {
        'Person': '1',
    },
    'mapping': [
        ['#!uuid', 'Person.id'],
        ['[*].village', 'Person.villageID'],
        ['$[*].name', 'Person.name'],
        ['$.data.people[*].dob', 'Person.dob.nested'],
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

EXAMPLE_DATA_FOR_NESTED_SCHEMA = [
    {
        'name': 'a',
        'lat': 10,
        'lng': 20
    },
    {
        'name': 'b',
        'lat': 11,
        'lng': 21
    },
    {
        'name': 'c',
        'lat': 12,
        'lng': 22
    },
]

EXAMPLE_REQUIREMENTS_NESTED_SCHEMA = {
    'Nested': {
        'name': '[*].name',
        'location.lat': '[*].lat',
        'location.lng': '[*].lng'
    }
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

EXAMPLE_REQUIREMENTS = {
    'Person': {
        'id': ['#!uuid'],
        'name': ['data.people[*].name'],
        'dob': ['data.people[*].dob'],
        'villageID': ['data.village'],
    },
}

EXAMPLE_REQUIREMENTS_ARRAY_BASE = {
    'Person': {
        'id': ['#!uuid'],
        'name': ['[*].name'],
        'dob': ['[*].dob'],
        'villageID': ['[*].village']
    }
}

EXAMPLE_ENTITY_DEFINITION = {
    'Person': [
        'id', '_rev', 'name', 'dob', 'villageID'
    ]
}

EXAMPLE_FIELD_MAPPINGS = [
    ['#!uuid', 'Person.id'],
    ['data.village', 'Person.villageID'],
    ['data.people[*].name', 'Person.name'],
    ['data.people[*].dob', 'Person.dob'],
]

EXAMPLE_FIELD_MAPPINGS_EDGE = [
    ['#!uuid', 'Person.id'],
    ['[*].village', 'Person.villageID'],
    ['$[*].name', 'Person.name'],
    ['$.data.people[*].dob', 'Person.dob.nested']
]

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

EXAMPLE_FIELD_MAPPINGS_ARRAY_BASE = [
    ['#!uuid', 'Person.id'],
    ['[*].village', 'Person.villageID'],
    ['[*].name', 'Person.name'],
    ['[*].dob', 'Person.dob'],
]

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
