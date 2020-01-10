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
