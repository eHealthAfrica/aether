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

import collections
import json
import os
import uuid

from unittest import TestCase
from spavro.schema import parse as parse_schema

from . import EXAMPLE_SCHEMA
from ..avro_tools import (
    # used in validation tests
    AvroValidationError as error,
    AvroValidationException,
    validate,

    # used in passthrough tests
    NAMESPACE,
    avro_schema_to_passthrough_artefacts as parser,

    # used in extractor tests
    is_nullable,
    __is_leaf as is_leaf,
    extract_jsonpaths_and_docs as extract,

    # used in random tests
    random_avro,
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
                    error(expected='null', datum='"not-null"', path='Test.test'),
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
                    error(expected='boolean', datum='"not-a-boolean"', path='Test.test'),
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
                    error(expected='bytes', datum='"not-bytes"', path='Test.test'),
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
                datum={'test': '1'},
                expected_errors=[
                    error(expected='int', datum='"1"', path='Test.test'),
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
                    error(expected='long', datum='"not-a-long"', path='Test.test'),
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
                    error(expected='float', datum='"not-a-float"', path='Test.test'),
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
                    error(expected='double', datum='"not-a-double"', path='Test.test'),
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
                    error(expected='md5', datum='"1234"', path='Test.test'),
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
                    error(expected='TestEnum', datum='"D"', path='Test.test'),
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
                    error(expected='int', datum='"not-an-int"', path='Test.test')
                ],
            ),
            AvroValidatorTest(
                fields=[{
                    'name': 'test',
                    'type': {
                        'type': 'map',
                        'values': 'int'
                    }
                }],
                datum={'test': 'not-a-map'},
                expected_errors=[
                    error(expected='map', datum='"not-a-map"', path='Test.test')
                ],
            ),
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
                    'name': 'a',
                    'type': [
                        'null',
                        {
                            'name': 'record-1',
                            'type': 'record',
                            'fields': [
                                {
                                    'name': 'b',
                                    'type': {
                                        'name': 'record-2',
                                        'type': 'record',
                                        'fields': [
                                            {
                                                'name': 'c',
                                                'type': ['null', 'string']
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ],
                }],
                datum={'a': {'b': {'c': 123}}},
                expected_errors=[
                    error(expected=['null', 'string'], datum=123, path='Test.a.b.c')
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
                datum={'test': 'not-a-record'},
                expected_errors=[
                    error(expected='TestRecord', datum='"not-a-record"', path='Test.test')
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


class TestAvroPassthrough(TestCase):

    def test__avro_schema_to_passthrough_artefacts__defaults(self):
        schema, mapping = parser(None, {'name': 'sample', 'type': 'record', 'fields': []})

        self.assertIsNotNone(schema['id'])
        # include namespace and id field
        self.assertEqual(schema['definition'], {
            'namespace': NAMESPACE,
            'name': 'sample',
            'type': 'record',
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
            'input': {},
            'schema': {
                'fields': [],
                'name': 'sample',
                'type': 'record'
            },
        })

    def test__avro_schema_to_passthrough_artefacts__non_defaults(self):
        schema, mapping = parser('1', {
            'name': 'sample2',
            'namespace': 'my.namespace',
            'type': 'record',
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
            'type': 'record',
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

        input = mapping.pop('input')
        self.assertIsNotNone(input)
        self.assertIn('id', input)
        self.assertTrue(isinstance(input['id'], int))
        self.assertIn('id2', input)
        self.assertTrue(isinstance(input['id2'], str))

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
            'schema': {
                'fields': [
                    {
                        'doc': 'My ID',
                        'name': 'id',
                        'type': 'int'
                    },
                    {
                        'doc': 'UUID',
                        'name': 'id2',
                        'type': 'string'
                    }
                ],
                'name': 'sample2',
                'namespace': 'my.namespace',
                'type': 'record'
            },
        })


class TestAvroRandom(TestCase):

    def test_random_avro__null(self):
        self.assertIsNone(random_avro({'type': 'null'}))

    def test_random_avro__boolean(self):
        self.assertTrue(isinstance(random_avro({'type': 'boolean'}), bool))

    def test_random_avro__int(self):
        self.assertTrue(isinstance(random_avro({'type': 'int'}), int))

    def test_random_avro__long(self):
        self.assertTrue(isinstance(random_avro({'type': 'long'}), int))

    def test_random_avro__float(self):
        self.assertTrue(isinstance(random_avro({'type': 'float'}), float))

    def test_random_avro__double(self):
        self.assertTrue(isinstance(random_avro({'type': 'double'}), float))

    def test_random_avro__string(self):
        self.assertTrue(isinstance(random_avro({'type': 'string'}), str))

    def test_random_avro__string__UUID(self):
        value = random_avro({'type': 'string', 'name': 'id'})
        self.assertTrue(isinstance(value, str))
        try:
            uuid.UUID(value)
            self.assertTrue(True)
        except ValueError:  # `value` is not a valid UUID
            self.assertTrue(False)

    def test_random_avro__bytes(self):
        self.assertTrue(isinstance(random_avro({'type': 'bytes'}), bytes))

    def test_random_avro__fixed(self):
        self.assertTrue(isinstance(random_avro({'type': 'fixed', 'size': 16}), bytes))

    def test_random_avro__enum(self):
        symbols = ['a', 'b', 'c']
        value = random_avro({'type': 'enum', 'symbols': symbols})
        self.assertTrue(isinstance(value, str))
        self.assertIn(value, symbols)

    def test_random_avro__record(self):
        value = random_avro({
            'type': 'record',
            'fields': [
                {
                    'name': 'a',
                    'type': 'null',
                },
                {
                    'name': 'b',
                    'type': 'null',
                },
                {
                    'name': 'c',
                    'type': 'null',
                },
            ]
        })
        self.assertEqual(value, {'a': None, 'b': None, 'c': None})

    def test_random_avro__map(self):
        value = random_avro({'type': 'map', 'values': 'int'})
        self.assertTrue(isinstance(value, dict))
        for k, v in value.items():
            self.assertTrue(isinstance(k, str))
            self.assertTrue(isinstance(v, int))

        symbols = ['a', 'b', 'c']
        value = random_avro({'type': 'map', 'values': {'type': 'enum', 'symbols': symbols}})
        for k, v in value.items():
            self.assertTrue(isinstance(k, str))
            self.assertTrue(isinstance(v, str))
            self.assertIn(v, symbols)

    def test_random_avro__array(self):
        value = random_avro({'type': 'array', 'items': 'int'})
        self.assertTrue(isinstance(value, list))
        for v in value:
            self.assertTrue(isinstance(v, int))

        symbols = ['a', 'b', 'c']
        value = random_avro({'type': 'array', 'items': {'type': 'enum', 'symbols': symbols}})
        self.assertTrue(isinstance(value, list))
        for v in value:
            self.assertTrue(isinstance(v, str))
            self.assertIn(v, symbols)

    def test_random_avro__union__nullable(self):
        self.assertTrue(isinstance(random_avro({'type': ['null', 'boolean']}), bool))
        self.assertTrue(isinstance(random_avro({'type': ['int', 'null']}), int))
        self.assertTrue(isinstance(random_avro({'type': ['null', {'type': 'fixed', 'size': 16}]}), bytes))

    def test_random_avro__union__not_nullable(self):
        value = random_avro({'type': ['boolean', 'null', 'int']})
        self.assertIsNotNone(value)
        self.assertTrue(isinstance(value, (int, bool)))

    def test_random_avro__named(self):
        self.assertIsNone(random_avro({'type': 'custom'}))

    def test_random_avro__complex(self):
        value = random_avro({
            'type': 'record',
            'fields': [
                {
                    'name': 'iterate',
                    'type': [
                        'null',
                        {
                            'type': 'array',
                            'items': {
                                'name': 'iterate',
                                'type': 'record',
                                'fields': [
                                    {
                                        'name': 'index',
                                        'type': ['null', 'int'],
                                    },
                                    {
                                        'name': 'value',
                                        'type': ['null', 'string'],
                                    },
                                ]
                            },
                        },
                    ],
                },
            ],
        })

        self.assertIsNotNone(value)
        self.assertTrue(isinstance(value, dict))
        self.assertIn('iterate', value)
        iterate = value['iterate']
        self.assertTrue(isinstance(iterate, list))
        self.assertTrue(len(iterate) > 0)
        for item in iterate:
            self.assertTrue(isinstance(item, dict))
            self.assertTrue(isinstance(item['index'], int))
            self.assertTrue(isinstance(item['value'], str))


class TestAvroExtractor(TestCase):

    def test__is_nullable(self):
        # should return false if type is not a union
        self.assertFalse(is_nullable({'type': 'array', 'items': 'another_type'}))
        self.assertFalse(is_nullable({'type': 'record'}))
        self.assertFalse(is_nullable({'type': 'map'}))
        self.assertFalse(is_nullable('null'))
        self.assertFalse(is_nullable({'type': 'null'}))

        # should return true only if type is a union fo two elements, one of them "null"
        self.assertFalse(is_nullable(['boolean', 'int']))
        self.assertFalse(is_nullable(['float', {'type': 'enum'}]))
        self.assertFalse(is_nullable(['string', 'int', {'type': 'record'}]))
        self.assertFalse(is_nullable(['null', 'int', {'type': 'record'}]))

        self.assertTrue(is_nullable(['null', 'int']))
        self.assertTrue(is_nullable(['null', {'type': 'enum'}]))

    def test__is_leaf(self):
        # should flag basic primitives as leaf
        self.assertTrue(is_leaf('null'))
        self.assertTrue(is_leaf('boolean'))
        self.assertTrue(is_leaf('int'))
        self.assertTrue(is_leaf('long'))
        self.assertTrue(is_leaf('float'))
        self.assertTrue(is_leaf('double'))
        self.assertTrue(is_leaf('bytes'))
        self.assertTrue(is_leaf('string'))
        self.assertTrue(is_leaf('enum'))
        self.assertTrue(is_leaf('fixed'))

        self.assertTrue(is_leaf({'type': 'null'}))
        self.assertTrue(is_leaf({'type': 'boolean'}))
        self.assertTrue(is_leaf({'type': 'int'}))
        self.assertTrue(is_leaf({'type': 'long'}))
        self.assertTrue(is_leaf({'type': 'float'}))
        self.assertTrue(is_leaf({'type': 'double'}))
        self.assertTrue(is_leaf({'type': 'bytes'}))
        self.assertTrue(is_leaf({'type': 'string'}))
        self.assertTrue(is_leaf({'type': 'enum'}))
        self.assertTrue(is_leaf({'type': 'fixed'}))

        # should not flag complex types
        self.assertFalse(is_leaf({'type': 'record'}))
        self.assertFalse(is_leaf({'type': 'map'}))
        self.assertFalse(is_leaf({'type': 'array', 'items': {'type': 'map'}}))
        self.assertFalse(is_leaf({'type': 'array', 'items': 'named_type'}))
        self.assertFalse(is_leaf(['null', 'int', {'type': 'record'}]))

        # should flag certain complex types
        self.assertTrue(is_leaf(['null', 'int']))
        self.assertTrue(is_leaf(['null', {'type': 'enum'}]))
        self.assertTrue(is_leaf({'type': 'array', 'items': 'long'}))

    def test__extract__with_doc(self):
        # should get take the "doc" property as doc
        schema = {
            'name': 'root',
            'doc': 'The root',
            'type': 'record',
            'fields': [
                {
                    'name': 'first',
                    'doc': 'The first',
                    # nullable primitive
                    'type': ['null', 'boolean']
                }
            ]
        }

        paths = []
        docs = {}
        extract(schema, paths, docs)

        self.assertEqual(paths, ['first'])
        self.assertEqual(docs, {'first': 'The first'})

    def test__extract__without_doc(self):
        # should no create any doc entry if no "doc"
        schema = {
            'name': 'root',
            'type': 'record',
            'fields': [
                {
                    'name': 'first',
                    # "enum" types are handled as primitives
                    'type': {
                        'name': 'coords',
                        # this is ignored, it belongs to the named type "coords"
                        'doc': '3D axes',
                        'type': 'enum',
                        'symbols': ['x', 'y', 'z']
                    }
                }
            ]
        }

        paths = []
        docs = {}
        extract(schema, paths, docs)

        self.assertEqual(paths, ['first'])
        self.assertEqual(docs, {})

    def test__extract__with_initial_values(self):
        # should not overwrite initial values
        schema = {
            'name': 'root',
            'doc': 'The root',
            'type': 'record',
            'fields': [
                {
                    'name': 'first',
                    'doc': 'The first',
                    'type': ['null', 'boolean']
                },
                {
                    'name': 'second',
                    'doc': 'The first',
                    'type': 'string'
                }
            ]
        }

        # initial paths and docs
        paths = ['zero', 'first']
        docs = {
            'unknown': 'who knows?',  # there is no path for it but...
            'first': 'The Second'
        }
        extract(schema, paths, docs)

        self.assertEqual(paths, ['zero', 'first', 'second'])
        self.assertEqual(docs, {
            'unknown': 'who knows?',  # still there
            'first': 'The Second',    # not replaced
            'second': 'The first',    # added
        })

    def test__extract__record_type(self):
        # should build nested paths
        schema = {
            'name': 'root',
            'doc': 'The root',
            'type': 'record',
            'fields': [
                {
                    'name': 'first',
                    'type': 'record',
                    'fields': [
                        {
                            'name': 'second',
                            'doc': 'leaf',
                            'type': ['null', 'boolean']
                        },
                        {
                            'name': 'fourth',
                            'type': [
                                'null',
                                {
                                    # it's the same name because it's nullable
                                    'name': 'fourth',
                                    'type': 'record',
                                    'fields': [
                                        {
                                            'name': 'fifth',
                                            'type': 'string'
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        paths = []
        docs = {}
        extract(schema, paths, docs)

        self.assertEqual(paths, ['first', 'first.second', 'first.fourth', 'first.fourth.fifth'])
        self.assertEqual(docs, {'first.second': 'leaf'})

    def test__extract__map_type(self):
        # should build map jsonpaths with "*"
        schema = {
            'name': 'root',
            'doc': 'The root',
            'type': 'record',
            'fields': [
                {
                    'name': 'a',
                    'type': 'record',
                    'fields': [
                        {
                            # it's the same name because it's nullable
                            'name': 'b',
                            'doc': 'Dictionary I',
                            'type': [
                                'null',
                                {
                                    'name': 'b',
                                    'type': 'map',
                                    'values': 'long'
                                }
                            ]
                        },
                        {
                            'name': 'c',
                            'doc': 'Dictionary II',
                            'type': 'map',
                            'values': {
                                'name': 'nullable_string',
                                'type': ['null', 'string']
                            }
                        },
                        {
                            'name': 'd',
                            'doc': 'Dictionary III (with children)',
                            'type': 'map',
                            'values': {
                                'name': 'it_does_not_matter',
                                'type': 'record',
                                'fields': [
                                    {
                                        'name': 'e',
                                        'doc': 'child',
                                        'type': 'string'
                                    }
                                ]
                            }
                        },
                        {
                            'name': 'f',
                            'doc': 'Dictionary IV',
                            'type': 'map',
                            'values': 'named_type'
                        }
                    ]
                }
            ]
        }

        paths = []
        docs = {}
        extract(schema, paths, docs)

        self.assertEqual(paths, [
            'a',
            'a.b',
            'a.b.*',
            'a.c',
            'a.c.*',
            'a.d',
            'a.d.*',
            'a.d.*.e',
            'a.f',
            'a.f.*',
        ])
        self.assertEqual(docs, {
            'a.b': 'Dictionary I',
            'a.c': 'Dictionary II',
            'a.d': 'Dictionary III (with children)',
            'a.d.*.e': 'child',
            'a.f': 'Dictionary IV',
        })

    def test__extract__array_type(self):
        # should build array jsonpaths with "#"
        schema = {
            'name': 'root',
            'doc': 'The root',
            'type': 'record',
            'fields': [
                {
                    'name': 'a',
                    'type': 'record',
                    'fields': [
                        {
                            'name': 'b',
                            'doc': 'List I',
                            'type': [
                                'null',
                                {
                                    # it's the same name because it's nullable
                                    'name': 'b',
                                    'type': 'array',
                                    'items': 'long'
                                }
                            ]
                        },
                        {
                            'name': 'c',
                            'doc': 'List II',
                            'type': 'array',
                            'items': {
                                'name': 'nullable_string',
                                'type': ['null', 'string']
                            }
                        },
                        {
                            'name': 'd',
                            'doc': 'List III (with children)',
                            'type': 'array',
                            'items': {
                                'name': 'it_does_not_matter',
                                'type': 'record',
                                'fields': [
                                    {
                                        'name': 'e',
                                        'doc': 'child',
                                        'type': 'string'
                                    }
                                ]
                            }
                        },
                        {
                            'name': 'f',
                            'doc': 'List IV',
                            'type': 'array',
                            'items': 'named_type'
                        }
                    ]
                }
            ]
        }

        paths = []
        docs = {}
        extract(schema, paths, docs)

        self.assertEqual(paths, [
            'a',
            'a.b',
            # 'a.b.#',  # array of primitives are treated as leafs
            'a.c',
            # 'a.c.#',  # array of primitives are treated as leafs
            'a.d',
            'a.d.#',
            'a.d.#.e',
            'a.f',
            'a.f.#',
        ])
        self.assertEqual(docs, {
            'a.b': 'List I',
            'a.c': 'List II',
            'a.d': 'List III (with children)',
            'a.d.#.e': 'child',
            'a.f': 'List IV',
        })

    def test__extract__union_type(self):
        # should build union jsonpaths as tagged unions
        schema = {
            'name': 'root',
            'doc': 'The root',
            'type': 'record',
            'fields': [
                {
                    'name': 'a',
                    'type': 'record',
                    'fields': [
                        {
                            'name': 'b',
                            'doc': 'Union I',
                            'type': [
                                'null',
                                'long',
                                'string',
                                {'name': 'axes', 'type': 'enum', 'symbols': ['x', 'y', 'z'], 'doc': 'axes'},
                                {'type': 'map', 'values': 'int', 'doc': 'coords'}
                            ]
                        }
                    ]
                }
            ]
        }

        paths = []
        docs = {}
        extract(schema, paths, docs)

        self.assertEqual(paths, [
            'a',
            'a.b',
            'a.b.?',
            'a.b.?.*',
        ])
        self.assertEqual(docs, {'a.b': 'Union I'})

    def test__extract__example(self):
        paths = []
        docs = {}
        extract(EXAMPLE_SCHEMA, paths, docs)

        self.assertEqual(paths, [
            'id',
            '_rev',
            'name',
            'dob',
            'villageID',
        ])
        self.assertEqual(docs, {
            'id': 'ID',
            '_rev': 'REVISION',
            'name': 'NAME',
            'villageID': 'VILLAGE',
        })
