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
from .. import utils


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
        error_message = mapping_validation.MESSAGE_NO_MATCH
        expected = mapping_validation.Failure(path, error_message)
        result = mapping_validation.validate_getter(submission_payload, path)
        self.assertEquals(expected, result)

    def test_validate_setter__success(self):
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': 'x'}},
                projectschema_name='Test-1',
                status='Publishable',
            ),
            utils.Entity(
                id=2,
                payload={'c': {'d': 'y'}},
                projectschema_name='Test-2',
                status='Publishable',
            ),
        ]
        path = 'Test-1.a.b'
        expected = mapping_validation.Success(path, ['x'])
        result = mapping_validation.validate_setter(entity_list, path)
        self.assertEquals(expected, result)

    def test_validate_setter__failure(self):
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': 'x'}},
                projectschema_name='Test-1',
                status='Publishable',
            ),
            utils.Entity(
                id=2,
                payload={'c': {'d': 'y'}},
                projectschema_name='Test-2',
                status='Publishable',
            ),
        ]
        path = 'Test-3.a.b'  # nonexistent project schema name "Test-3"
        error_message = mapping_validation.MESSAGE_NO_MATCH
        expected = mapping_validation.Failure(path, error_message)
        result = mapping_validation.validate_setter(entity_list, path)
        self.assertEquals(expected, result)

    def test_validate_mapping__success(self):
        submission_payload = {'a': {'b': 'x'}, 'c': {'d': 'y'}}
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': 'c'}},
                projectschema_name='Test-1',
                status='Publishable',
            ),
            utils.Entity(
                id=2,
                payload={'c': {'d': 'y'}},
                projectschema_name='Test-2',
                status='Publishable',
            ),
        ]
        mapping_definition = {
            'mapping': [
                ('$.a.b', 'Test-1.a.b'),
                ('$.c.d', 'Test-2.c.d'),
            ]
        }
        expected = []
        result = mapping_validation.validate_mappings(
            submission_payload, entity_list, mapping_definition,
        )
        self.assertEquals(expected, result)

    def test_validate_mapping__wildcard_success(self):
        submission_payload = {'data': {'a1': {'b': 'x'}, 'a2': {'d': 'y'}}}
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': [{'b': 'x'}, {'d': 'y'}]}},
                projectschema_name='Test-1',
                status='Publishable',
            )
        ]
        mapping_definition = {
            'mapping': [
                ('$.data.a*', 'Test-1.a.b')
            ]
        }
        expected = []
        result = mapping_validation.validate_mappings(
            submission_payload, entity_list, mapping_definition,
        )
        self.assertEquals(expected, result)

    def test_validate_mapping__failure(self):
        submission_payload = {'a': {'b': 'x'}, 'c': {'d': 'y'}}
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': 'c'}},
                projectschema_name='Test-1',
                status='Publishable',
            ),
            utils.Entity(
                id=2,
                payload={'c': {'d': 'y'}},
                projectschema_name='Test-2',
                status='Publishable',
            ),
        ]
        mapping_definition = {
            'mapping': [
                ('$.a.b', 'Test-1.nonexistent'),
                ('$.nonexistent', 'Test-2.c.d'),
            ]
        }
        expected = [
            mapping_validation.Failure(
                path=mapping_definition['mapping'][0][1],
                error_message=mapping_validation.MESSAGE_NO_MATCH,
            ),
            mapping_validation.Failure(
                path=mapping_definition['mapping'][1][0],
                error_message=mapping_validation.MESSAGE_NO_MATCH,
            ),
        ]
        result = mapping_validation.validate_mappings(
            submission_payload, entity_list, mapping_definition,
        )
        self.assertEquals(expected, result)
