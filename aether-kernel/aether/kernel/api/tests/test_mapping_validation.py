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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.test import TestCase
from .. import mapping_validation

valid_schemas = {
    'Person': {
        'name': 'Person',
        'type': 'record',
        'fields': [
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
            }
        ]
    }
}

invalid_schemas = {
    'Person': {
        'name': 'Person',
        'type': 'record',
        'fields': [
            {
                'invalidField': 1
            }
        ]
    }
}


class TestMappingValidation(TestCase):

    def test_validate_getter__success_1(self):
        submission_payload = {'a': {'b': 'x'}}
        path = '#!uuid'
        expected = mapping_validation.Success(path, [])
        result = mapping_validation.validate_getter(submission_payload, path)
        self.assertEquals(expected, result)

    def test_validate_getter__success_2(self):
        submission_payload = {'a': {'b': 'x'}}
        path = '$.a.b'
        expected = mapping_validation.Success(path, ['x'])
        result = mapping_validation.validate_getter(submission_payload, path)
        self.assertEquals(expected, result)

    def test_validate_getter__failure(self):
        submission_payload = {'a': {'b': 'x'}}
        path = '$.d.e'
        description = mapping_validation.NO_MATCH
        expected = mapping_validation.Failure(path, description)
        result = mapping_validation.validate_getter(submission_payload, path)
        self.assertEquals(expected, result)

    def test_validate_setter__success(self):
        path = 'Person.firstName'
        expected = mapping_validation.Success(path, [])
        result = mapping_validation.validate_setter(valid_schemas, path)
        self.assertEquals(expected, result)

    def test_validate_setter__failure__invalid_path(self):
        path = 'a.b.c'
        description = mapping_validation.INVALID_PATH
        expected = mapping_validation.Failure(path, description)
        result = mapping_validation.validate_setter(valid_schemas, path)
        self.assertEquals(expected, result)

    def test_validate_setter__failure__invalid_schema(self):
        path = 'Person.firstName'
        description = mapping_validation.invalid_schema('Person')
        expected = mapping_validation.Failure(path, description)
        result = mapping_validation.validate_setter(invalid_schemas, path)
        self.assertEquals(expected, result)

    def test_validate_setter__failure__no_match(self):
        path = 'Person.nonexistentField'
        description = mapping_validation.NO_MATCH
        expected = mapping_validation.Failure(path, description)
        result = mapping_validation.validate_setter(valid_schemas, path)
        self.assertEquals(expected, result)

    def test_validate_setter__failure__no_schema(self):
        path = 'NonexistantSchema.firstName'
        description = mapping_validation.no_schema('NonexistantSchema')
        expected = mapping_validation.Failure(path, description)
        result = mapping_validation.validate_setter(valid_schemas, path)
        self.assertEquals(expected, result)

    def test_validate_mapping__success(self):
        submission_payload = {'a': {'b': 'x'}, 'c': {'d': 'y'}}
        mapping_definition = {
            'mapping': [
                ('$.a.b', 'Person.firstName'),
                ('$.c.d', 'Person.lastName'),
            ]
        }
        expected = []
        result = mapping_validation.validate_mappings(
            submission_payload, valid_schemas, mapping_definition,
        )
        self.assertEquals(expected, result)

    def test_validate_mapping__wildcard_success(self):
        submission_payload = {'data': {'a1': {'b': 'x'}, 'a2': {'d': 'y'}}}
        mapping_definition = {
            'mapping': [
                ('$.data.a*', 'Person.firstName')
            ]
        }
        expected = []
        result = mapping_validation.validate_mappings(
            submission_payload, valid_schemas, mapping_definition,
        )
        self.assertEquals(expected, result)

    def test_validate_mapping__failure(self):
        submission_payload = {'a': {'b': 'x'}, 'c': {'d': 'y'}}
        mapping_definition = {
            'mapping': [
                ('$.a.b', 'Test-1.nonexistent'),
                ('$.nonexistent', 'Test-2.c.d'),
            ]
        }
        expected = [
            mapping_validation.Failure(
                path=mapping_definition['mapping'][0][1],
                description=mapping_validation.no_schema('Test-1'),
            ),
            mapping_validation.Failure(
                path=mapping_definition['mapping'][1][0],
                description=mapping_validation.NO_MATCH,
            ),
            mapping_validation.Failure(
                path=mapping_definition['mapping'][1][1],
                description=mapping_validation.INVALID_PATH,
            ),
        ]
        result = mapping_validation.validate_mappings(
            submission_payload, valid_schemas, mapping_definition,
        )
        self.assertEquals(expected, result)
