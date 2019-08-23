# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from unittest import TestCase

from .. import validators
from . import NESTED_ARRAY_SCHEMA


class ValidatorsTest(TestCase):

    def setUp(self):
        self.schema = {
            'name': 'Test',
            'type': 'record',
            'fields': [
                {'name': 'name', 'type': 'string'},
                {'name': 'age', 'type': 'int'},
                {'name': 'id', 'type': 'string'},
            ]
        }
        self.nested_schema = NESTED_ARRAY_SCHEMA

    def test_validate_entities__error(self):
        entity_list = [
            {},
            {'a_string': 1},
            {'a': 'b'},
        ]
        entities = {
            'Test': entity_list,
        }
        schemas = {
            'Test': {
                'name': 'Test',
                'type': 'record',
                'fields': [
                    {
                        'name': 'a_string',
                        'type': 'string'
                    }
                ],
            },
        }
        result = validators.validate_entities(entities=entities, schemas=schemas)
        self.assertEqual(len(result.validation_errors), len(entity_list) * 2)
