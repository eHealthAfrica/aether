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
from django.core.exceptions import ValidationError

from aether.kernel.api import validators
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

    def test_validate_schema_definition__success(self):
        try:
            validators.validate_schema_definition(self.schema)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

    def test_validate_avro_schema__success(self):
        try:
            validators.validate_avro_schema(self.schema)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

    def test_validate_avro_schema__error(self):
        with self.assertRaises(ValidationError) as err:
            validators.validate_avro_schema({})  # "{}" is not a valid Avro schema
        message = str(err.exception)
        self.assertIn('No "type" property', message)

    def test_validate_id_field__success(self):
        try:
            validators.validate_id_field(self.schema)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

    def test_validate_id_field__success__union(self):
        try:
            validators.validate_id_field([
                {'name': 'Test1', 'type': 'record', 'fields': []},
                {'name': 'Test2', 'type': 'record', 'fields': []},
                {**self.schema, 'aetherBaseSchema': True}
            ])
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

    def test_validate_id_field__error(self):
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
        with self.assertRaises(ValidationError) as err:
            validators.validate_id_field(invalid_schema)
        message = str(err.exception)
        self.assertIn(validators.MESSAGE_REQUIRED_ID, message)

    def test_validate_id_field__error__union(self):
        missing_aetherBaseSchema = [
            {'name': 'Test1', 'type': 'record'},
            {'name': 'Test2', 'type': 'record'},
            {'name': 'Test3', 'type': 'record'},
        ]
        with self.assertRaises(ValidationError) as err:
            validators.validate_id_field(missing_aetherBaseSchema)
        message = str(err.exception)
        self.assertIn(validators.MESSAGE_REQUIRED_ID, message)

        more_than_one_aetherBaseSchema = [
            {'name': 'Test1', 'type': 'record', 'aetherBaseSchema': True},
            {'name': 'Test2', 'type': 'record'},
            {'name': 'Test3', 'type': 'record', 'aetherBaseSchema': True},
        ]
        with self.assertRaises(ValidationError) as err:
            validators.validate_id_field(more_than_one_aetherBaseSchema)
        message = str(err.exception)
        self.assertIn(validators.MESSAGE_REQUIRED_ID, message)

        one_aetherBaseSchema__missing_id = [
            {'name': 'Test1', 'type': 'record'},
            {'name': 'Test2', 'type': 'record'},
            {'name': 'Test3', 'type': 'record', 'aetherBaseSchema': True},
        ]
        with self.assertRaises(ValidationError) as err:
            validators.validate_id_field(one_aetherBaseSchema__missing_id)
        message = str(err.exception)
        self.assertIn(validators.MESSAGE_REQUIRED_ID, message)

    def test_validate_mapping_definition__success(self):
        mappings = [
            {},
            {
                'entities': {'Person': str(uuid.uuid4())},
                'mapping': [['$.a', 'Person.a']],
            },
            {
                'entities': {'Person': str(uuid.uuid4())},
                'mapping': [['[*].a', 'Person.a']],
            },
        ]
        for mapping in mappings:
            try:
                validators.validate_mapping_definition(mapping)
                self.assertTrue(True)
            except Exception:
                self.assertTrue(False)

    def test_validate_mapping_definition__error(self):
        mappings = [
            {'mapping': [['$.a', 'Person.a']]},
            {'entities': {'Person': str(uuid.uuid4())}},
            {'a': 1},
        ]
        for mapping in mappings:
            with self.assertRaises(ValidationError) as err:
                validators.validate_mapping_definition(mapping)
            self.assertIn(
                'is not valid under any of the given schemas',
                str(err.exception),
            )

    def test_validate_schemas__success(self):
        schemas = {
            'one': self.schema,
            'two': self.nested_schema,
        }
        try:
            validators.validate_schemas(schemas)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

    def test_validate_schemas__error(self):
        with self.assertRaises(ValidationError) as err:
            validators.validate_schemas([self.schema])
        message = str(err.exception)
        self.assertIn(' is not an Object', message)

    def test_validate_entity_payload__success(self):
        schema_definition = {
            'name': 'Test',
            'type': 'record',
            'fields': [
                {
                    'name': 'a_string',
                    'type': 'string',
                },
            ],
        }
        payload = {'a_string': 'test'}
        result = validators.validate_entity_payload(
            schema_definition=schema_definition,
            payload=payload,
        )
        self.assertTrue(result)

    def test_validate_entity_payload__error(self):
        schema_definition = {
            'name': 'Test',
            'type': 'record',
            'fields': [
                {
                    'name': 'a_string',
                    'type': 'string'
                }
            ],
        }
        payloads = [
            {},
            {'a_string': 1},
            {'a': 'b'},
        ]
        for payload in payloads:
            with self.assertRaises(ValidationError) as err:
                validators.validate_entity_payload(
                    schema_definition=schema_definition,
                    payload=payload,
                )
            msg = 'did not conform to registered schema'
            self.assertIn(msg, err.exception.args[0])

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
