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

import uuid

from django.test import TestCase
from rest_framework import serializers

from aether.kernel.api import validators


class ValidatorsTest(TestCase):

    def setUp(self):
        self.schema = {
            'name': 'Test',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                }
            ]
        }

    def test_validate_avro_schema__success(self):
        result = validators.validate_avro_schema(self.schema)
        self.assertIsNone(result)

    def test_validate_avro_schema__error(self):
        with self.assertRaises(serializers.ValidationError) as err:
            validators.validate_avro_schema({})  # "{}" is not a valid Avro schema
        message = str(err.exception.detail[0])
        self.assertIn('No "type" property', message)

    def test_has_valid_id_field__success(self):
        result = validators.validate_id_field(self.schema)
        self.assertIsNone(result)

    def test_has_valid_id_field__error(self):
        invalid_schema = {
            'name': 'Test',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'int'  # "id" has to be of type "string"
                }
            ]
        }
        with self.assertRaises(serializers.ValidationError) as err:
            validators.validate_id_field(invalid_schema)
        message = str(err.exception.detail[0])
        self.assertIn(validators.MESSAGE_REQUIRED_ID, message)

    def test_validate_mapping_definition__success(self):
        mappings = [
            {},
            {
                'entities': {'Person': str(uuid.uuid4())},
                'mapping': [['$.a', 'Person.a']],
            },
        ]
        for mapping in mappings:
            result = validators.validate_mapping_definition(mapping)
            self.assertIsNone(result)

    def test_validate_mapping_definition__error(self):
        mappings = [
            {'mapping': [['$.a', 'Person.a']]},
            {'entities': {'Person': str(uuid.uuid4())}},
            {'a': 1},
        ]
        for mapping in mappings:
            with self.assertRaises(serializers.ValidationError) as err:
                validators.validate_mapping_definition(mapping)
            self.assertIn(
                'is not valid under any of the given schemas',
                err.exception.detail[0],
            )
