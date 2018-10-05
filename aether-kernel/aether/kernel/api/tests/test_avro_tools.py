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

import collections
import json
import os

from django.test import TestCase
from spavro.schema import parse as parse_schema

from aether.kernel.api.avro_tools import (
    avro_schema_to_passthrough_artefacts as parser,
    AvroValidationError as error,
    AvroValidationException,
    validate,
    NAMESPACE,
)

here = os.path.dirname(os.path.realpath(__file__))

# This namedtuple represents an avro validation test.
# Fields:
#     - fields: a list of avro schema fields. Used in
#       TestAvroValidator.run_validation_tests().
#     - datum: the value to test.
#     - expected_errors: a list of expected errors.
AvroValidatorTest = collections.namedtuple(
    'AvroTest',
    ['fields', 'datum', 'expected_errors'],
)


class TestAvroValidator(TestCase):

    def run_validation_tests(self, tests):
        for test in tests:
            schema = {'type': 'record', 'name': 'Test', 'fields': test.fields}
            spavro_schema = parse_schema(json.dumps(schema))
            result = validate(spavro_schema, test.datum)
            if result.errors:
                self.assertFalse(result.is_valid)
            else:
                self.assertTrue(result.is_valid)
            self.assertEqual(test.expected_errors, result.errors)

    def test_validate_null(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'null'}],
                datum={'test': None},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'null'}],
                datum={'test': 'not-null'},
                expected_errors=[
                    error(expected='null', datum='not-null', path='Test.test'),
                ],
            ),
        ])

    def test_validate_boolean(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'boolean'}],
                datum={'test': True},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'boolean'}],
                datum={'test': 'not-a-boolean'},
                expected_errors=[
                    error(expected='boolean', datum='not-a-boolean', path='Test.test'),
                ],
            )
        ])

    def test_validate_bytes(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'bytes'}],
                datum={'test': bytes(1)},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'bytes'}],
                datum={'test': 'not-bytes'},
                expected_errors=[
                    error(expected='bytes', datum='not-bytes', path='Test.test'),
                ],
            )
        ])

    def test_validate_string(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'string'}],
                datum={'test': 'a-string'},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'string'}],
                datum={'test': None},
                expected_errors=[
                    error(expected='string', datum=None, path='Test.test'),
                ],
            )
        ])

    def test_validate_int(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'int'}],
                datum={'test': 1},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'int'}],
                datum={'test': 'not-an-int'},
                expected_errors=[
                    error(expected='int', datum='not-an-int', path='Test.test'),
                ],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'int'}],
                datum={'test': 999999999999999999},
                expected_errors=[
                    error(expected='int', datum=999999999999999999, path='Test.test'),
                ],
            )
        ])

    def test_validate_long(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'long'}],
                datum={'test': 999999999999999999},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'long'}],
                datum={'test': 'not-a-long'},
                expected_errors=[
                    error(expected='long', datum='not-a-long', path='Test.test'),
                ],
            )
        ])

    def test_validate_float(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'float'}],
                datum={'test': 1.2},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'float'}],
                datum={'test': 'not-a-float'},
                expected_errors=[
                    error(expected='float', datum='not-a-float', path='Test.test'),
                ],
            ),
        ])

    def test_validate_double(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'double'}],
                datum={'test': 1.2},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{'name': 'test', 'type': 'double'}],
                datum={'test': 'not-a-double'},
                expected_errors=[
                    error(expected='double', datum='not-a-double', path='Test.test'),
                ],
            )
        ])

    def test_validate_fixed(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'type': 'fixed',
                        'size': 32,
                        'name': 'md5'
                    }
                }],
                datum={'test': 'd41d8cd98f00b204e9800998ecf8427e'},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'type': 'fixed',
                        'size': 32,
                        'name': 'md5'
                    }
                }],
                datum={'test': '1234'},
                expected_errors=[
                    error(expected='md5', datum='1234', path='Test.test'),
                ],
            )
        ])

    def test_validate_enum(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'name': 'TestEnum',
                        'type': 'enum',
                        'symbols': ['A', 'B', 'C']
                    }
                }],
                datum={'test': 'A'},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'name': 'TestEnum',
                        'type': 'enum',
                        'symbols': ['A', 'B', 'C']
                    }
                }],
                datum={'test': 'D'},
                expected_errors=[
                    error(expected='TestEnum', datum='D', path='Test.test'),
                ],
            )
        ])

    def test_validate_array(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'type': 'array',
                        'items': 'string'
                    }
                }],
                datum={'test': ['a-string']},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'type': 'array',
                        'items': 'string'
                    }
                }],
                datum={'test': None},
                expected_errors=[
                    error(expected='array', datum=None, path='Test.test'),
                ],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'type': 'array',
                        'items': 'string'
                    }
                }],
                datum={'test': ['a-string', 1]},
                expected_errors=[
                    error(expected='string', datum=1, path='Test.test[1]'),
                ],
            )
        ])

    def test_validate_map(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'type': 'map',
                        'values': 'int'
                    }
                }],
                datum={'test': {'a': 1}},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'type': 'map',
                        'values': 'int'
                    }
                }],
                datum={'test': {'a': 'not-an-int'}},
                expected_errors=[
                    error(expected='int', datum='not-an-int', path='Test.test')
                ],
            )
        ])

    def test_validate_union(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': ['null', 'string'],
                }],
                datum={'test': None},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': ['null', 'string'],
                }],
                datum={'test': 'a-string'},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': ['null', 'string'],
                }],
                datum={'test': 1},
                expected_errors=[
                    error(expected=['null', 'string'], datum=1, path='Test.test')
                ],
            ),
        ])

    def test_validate_record(self):
        self.run_validation_tests([
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'name': 'TestRecord',
                        'type': 'record',
                        'fields': [
                            {
                                'name': 'a',
                                'type': 'string'
                            },
                            {
                                'name': 'b',
                                'type': 'int'
                            },
                            {
                                'name': 'c',
                                'type': {
                                    'type': 'array',
                                    'items': 'string'
                                }
                            }
                        ]
                    }
                }],
                datum={'test': {'a': 'a-string', 'b': 1, 'c': ['a-string']}},
                expected_errors=[],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'name': 'TestRecord',
                        'type': 'record',
                        'fields': [
                            {
                                'name': 'a',
                                'type': 'string'
                            },
                            {
                                'name': 'b',
                                'type': 'int'
                            },
                            {
                                'name': 'c',
                                'type': {
                                    'type': 'array',
                                    'items': 'string'
                                }
                            }
                        ]
                    }
                }],
                datum={'test': {'a': 1, 'b': ['a-string'], 'c': ['a-string', 2]}},
                expected_errors=[
                    error(expected='string', datum=1, path='Test.test.a'),
                    error(expected='int', datum=['a-string'], path='Test.test.b'),
                    error(expected='string', datum=2, path='Test.test.c[1]'),
                ],
            ),
        ])

    def test_validate_recursive__success(self):
        with open(os.path.join(here, 'files/avrodoc.avsc'), 'r') as infile:
            schema = json.load(infile)
        spavro_schema = parse_schema(json.dumps(schema))
        datum = {
            'id': 123,
            'username': 'Foo',
            'passwordHash': 'bar',
            'signupDate': 1528879144000,
            'emailAddresses': [{
                'address': 'foo@example.com',
                'verified': True,
                'dateAdded': 1528879144000,
            }],
            'twitterAccounts': [],
            'toDoItems': [
                {
                    'status': 'ACTIONABLE',
                    'title': '1',
                    'description': 'abc',
                    'snoozeDate': 1528879144000,
                    'subItems': [
                        {
                            'status': 'HIDDEN',
                            'title': '1.1',
                            'description': 'abc',
                            'snoozeDate': 1528879144000,
                            'subItems': [
                            ]
                        },
                        {
                            'status': 'DONE',
                            'title': '1.2',
                            'description': 'abc',
                            'snoozeDate': 1528879144000,
                            'subItems': [
                                {
                                    'status': 'DELETED',
                                    'title': '1.2.1',
                                    'description': 'abc',
                                    'snoozeDate': 1528879144000,
                                    'subItems': [
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        result = validate(spavro_schema, datum)
        expected_errors = []
        self.assertEqual(expected_errors, result.errors)

    def test_validate_recursive__error(self):
        with open(os.path.join(here, 'files/avrodoc.avsc'), 'r') as infile:
            schema = json.load(infile)
        spavro_schema = parse_schema(json.dumps(schema))
        datum = {
            'id': 123,
            'username': 'Foo',
            'passwordHash': 'bar',
            'signupDate': 1528879144000,
            'emailAddresses': [{
                'address': 'foo@example.com',
                'verified': True,
                'dateAdded': 1528879144000,
            }],
            'twitterAccounts': [],
            'toDoItems': [
                {
                    'status': None,  # Not a valid status
                    'title': '1',
                    'description': 'abc',
                    'snoozeDate': 1528879144000,
                    'subItems': [
                        {
                            'status': 'HIDDEN',
                            'title': 1.1,  # Not a string
                            'description': 'abc',
                            'snoozeDate': 1528879144000,
                            'subItems': []
                        },
                        {
                            'status': 'DONE',
                            'title': '1.2',
                            'description': ['test'],  # Not a string
                            'snoozeDate': 1,
                            'subItems': [
                                {
                                    'status': 'DELETED',
                                    'title': 4,
                                    'description': 'abc',
                                    'snoozeDate': 1,  # Not a long
                                    'subItems': []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        result = validate(spavro_schema, datum)
        expected_errors = [
            error(
                expected='ToDoStatus',
                datum=None,
                path='User.toDoItems[0].status',
            ),
            error(
                expected='string',
                datum=1.1,
                path='User.toDoItems[0].subItems[0].title',
            ),
            error(
                expected=['null', 'string'],
                datum=['test'],
                path='User.toDoItems[0].subItems[1].description',
            ),
            error(
                expected='string',
                datum=4,
                path='User.toDoItems[0].subItems[1].subItems[0].title',
            )
        ]
        self.assertEqual(expected_errors, result.errors)

    def test_validate_top_level_union__success(self):
        spavro_schema = parse_schema(json.dumps(['null', 'string']))
        datum = 'a-string'
        result = validate(spavro_schema, datum)
        expected_errors = []
        self.assertTrue(result.is_valid)
        self.assertEqual(expected_errors, result.errors)

    def test_validate_top_level_union__error(self):
        spavro_schema = parse_schema(json.dumps(['null', 'string']))
        datum = 1
        result = validate(spavro_schema, datum)
        expected_errors = [
            error(expected=['null', 'string'], datum=1, path='$')
        ]
        self.assertFalse(result.is_valid)
        self.assertEqual(expected_errors, result.errors)

    def test_validate__raises(self):
        Schema = collections.namedtuple('Schema', ['type'])
        schema = Schema('not-an-avro-type')
        with self.assertRaises(AvroValidationException) as err:
            validate(schema, 2)
        message = str(err.exception)
        self.assertIn('Could not validate', message)


class TestAvroTools(TestCase):

    def test__avro_schema_to_passthrough_artefacts__defaults(self):
        schema, mapping = parser(None, {'name': 'sample', 'fields': []})

        self.assertIsNotNone(schema['id'])
        # include namespace and id field
        self.assertEqual(schema['definition'], {
            'namespace': NAMESPACE,
            'name': 'sample',
            'fields': [
                {
                    'doc': 'UUID',
                    'name': 'id',
                    'type': 'string',
                },
            ]
        })

        self.assertEqual(mapping, {
            'id': schema['id'],
            'name': 'sample',
            'definition': {
                'entities': {'sample': schema['id']},
                'mapping': [['#!uuid', 'sample.id']],
            },
            'is_read_only': True,
            'is_active': True,
        })

    def test__avro_schema_to_passthrough_artefacts__non_defaults(self):
        schema, mapping = parser('1', {
            'name': 'sample2',
            'namespace': 'my.namespace',
            'fields': [
                {
                    'doc': 'My ID',
                    'name': 'id',
                    'type': 'int',
                },
                {
                    'doc': 'UUID',
                    'name': 'id2',
                    'type': 'string',
                },
            ]
        })

        self.assertEqual(schema['id'], '1')
        self.assertEqual(schema['definition'], {
            'namespace': 'my.namespace',
            'name': 'sample2',
            'fields': [
                {
                    'doc': 'My ID',
                    'name': 'id',
                    'type': 'int',
                },
                {
                    'doc': 'UUID',
                    'name': 'id2',
                    'type': 'string',
                },
            ]
        })

        self.assertEqual(mapping, {
            'id': '1',
            'name': 'sample2',
            'definition': {
                'entities': {'sample2': '1'},
                'mapping': [
                    ['$.id', 'sample2.id'],
                    ['$.id2', 'sample2.id2'],
                ],
            },
            'is_read_only': True,
            'is_active': True,
        })
