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

from .. import utils
from . import (EXAMPLE_MAPPING, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA,
               EXAMPLE_NESTED_SOURCE_DATA, EXAMPLE_REQUIREMENTS,
               EXAMPLE_ENTITY_DEFINITION, EXAMPLE_FIELD_MAPPINGS, EXAMPLE_ENTITY)


class UtilsTests(TestCase):

    def test_json_prettified_simple(self):
        data = {}
        expected = '<pre><span></span><span class="p">{}</span>\n</pre>'
        pretty = str(utils.json_prettified(data))
        self.assertTrue(expected in pretty, pretty)

    def test_code_prettified_simple(self):
        data = 'print "Hello world!"'
        expected = '<span class="s2">&quot;Hello world!&quot;</span>'

        pretty = str(utils.code_prettified(data))
        self.assertTrue(expected in pretty, pretty)

    def test_json_printable(self):
        data = [{'dob': '2000-01-01', 'name': 'PersonA'}]
        expected = [{'dob': '2000-01-01', 'name': 'PersonA'}]
        printable = utils.json_printable(data)
        self.assertEquals(printable, expected)

    def test_json_printable_other_obj(self):
        data = 2
        expected = 2
        printable = utils.json_printable(data)
        self.assertEquals(printable, expected)

    def test_get_field_mappings(self):
        mapping = EXAMPLE_MAPPING
        expected = EXAMPLE_FIELD_MAPPINGS
        field_mapping = str(utils.get_field_mappings(mapping))
        self.assertTrue(str(expected) in field_mapping, field_mapping)

    def test_JSP_get_basic_fields(self):
        avro_obj = EXAMPLE_SCHEMA
        expected = ['id', '_rev', 'name', 'dob', 'villageID']
        basic_fields = str(utils.JSP_get_basic_fields(avro_obj))
        self.assertTrue(str(expected) in basic_fields, basic_fields)

    def test_get_entity_definitions(self):
        entity_type = 'Person'
        mapping = EXAMPLE_MAPPING
        schema = {entity_type: EXAMPLE_SCHEMA}
        expected = EXAMPLE_ENTITY_DEFINITION
        entity_definition = str(utils.get_entity_definitions(mapping, schema))
        self.assertTrue(str(expected) in entity_definition, entity_definition)

    def test_get_entity_requirements(self):
        entities = EXAMPLE_ENTITY_DEFINITION
        field_mappings = EXAMPLE_FIELD_MAPPINGS
        expected = EXAMPLE_REQUIREMENTS
        entity_requirements = str(
            utils.get_entity_requirements(entities, field_mappings))
        self.assertTrue(str(expected) in entity_requirements,
                        entity_requirements)

    def test_get_entity_stub(self):
        requirements = EXAMPLE_REQUIREMENTS
        source_data = EXAMPLE_SOURCE_DATA
        entity_definitions = EXAMPLE_ENTITY_DEFINITION
        entity_name = 'Person'
        stub = utils.get_entity_stub(
            requirements, entity_definitions, entity_name, source_data)
        self.assertEquals(len(stub.get('dob')), 3)

    def test_resolve_source_reference__single_resolution(self):
        data = EXAMPLE_SOURCE_DATA
        requirements = EXAMPLE_REQUIREMENTS
        entities = EXAMPLE_ENTITY
        entity_name = 'Person'
        field = 'villageID'
        path = requirements.get(entity_name, {}).get(field)[0]
        resolved_count = utils.resolve_source_reference(
            path, entities, entity_name, 0, field, data)
        self.assertEquals(resolved_count, 1)

    def test_resolve_source_reference__multiple_resolutions(self):
        data = EXAMPLE_SOURCE_DATA
        requirements = EXAMPLE_REQUIREMENTS
        entities = EXAMPLE_ENTITY
        entity_name = 'Person'
        field = 'dob'
        path = requirements.get(entity_name, {}).get(field)[0]
        resolved_count = utils.resolve_source_reference(
            path, entities, entity_name, 0, field, data)
        self.assertEquals(resolved_count, 3)

    def test_resolve_source_reference__wildcard_resolutions(self):
        data = EXAMPLE_SOURCE_DATA
        entities = EXAMPLE_ENTITY
        entity_name = 'Person'
        field = 'dob'
        path = 'data.pe*[*].dob'
        resolved_count = utils.resolve_source_reference(
            path, entities, entity_name, 0, field, data)
        self.assertEquals(resolved_count, 3)

    def test_object_contains(self):
        data = EXAMPLE_NESTED_SOURCE_DATA
        source_house = data['data']['houses'][0]
        other_house = data['data']['houses'][1]
        test_person = source_house['people'][0]
        is_included = utils.object_contains(test_person, source_house)
        not_included = utils.object_contains(test_person, other_house)
        self.assertTrue(is_included), 'Person should be found in this house.'
        self.assertFalse(
            not_included), 'Person should not found in this house.'

    def test_coercion(self):
        test_cases = [    
            ('a', 'string', 'a'),
            ('true', 'boolean', True),
            ('True', 'boolean', True),
            ('T', 'boolean', True),
            ('0', 'boolean', True),
            (0, 'boolean', False),
            (1, 'string', '1'),
            ('1', 'json', 1),
            (1, 'int', 1),
            ('1', 'int', 1),
            ('1.00', 'float', 1.00),
            ('["a"]', 'json', ['a']),
            ('{"hold": ["a"]}', 'json', {"hold": ["a"]}),
            ('poop', 'float', 1.00),
        ]
        for t in test_cases:
            res = utils.coercion(t[0], t[1])
            self.assertTrue(res == t[2])

    def test_action_constant(self):
        args = ['154', 'int']
        assertTrue(utils.action_constant(args) == 154)

    def test_anchor_references(self):
        source_data = EXAMPLE_NESTED_SOURCE_DATA
        source = 'data.houses[*].people[*]'
        context = 'data.houses[*]'
        instance_number = 5
        idx = utils.anchor_reference(
            source, context, source_data, instance_number)
        self.assertEquals(idx, 1), 'Person #5 be found in second house, index @ 1'

    def test_get_or_make_uuid(self):
        entity_type = 'Person'
        field_name = '_id'
        instance_number = 0
        source_data = EXAMPLE_SOURCE_DATA
        uuid = str(utils.get_or_make_uuid(
            entity_type, field_name, instance_number, source_data))
        self.assertEquals(uuid.count('-'), 4)

    def test_extract_entity(self):
        requirements = EXAMPLE_REQUIREMENTS
        response_data = EXAMPLE_SOURCE_DATA
        entity_definitions = EXAMPLE_ENTITY_DEFINITION
        expected_entity = EXAMPLE_ENTITY
        entities = {'Person': []}
        entity_name = 'Person'
        entity_stub = utils.get_entity_stub(
            requirements, entity_definitions, entity_name, response_data
        )
        failed_actions = utils.extract_entity(
            entity_name, entities, requirements, response_data, entity_stub
        )
        self.assertEquals(
            len(expected_entity['Person']), len(entities['Person']))
        self.assertEquals(len(failed_actions), 0)

    def test_extract_entities(self):
        '''
        Assert that the number of extracted entities equals the
        number of Persons in the source data.
        '''
        requirements = EXAMPLE_REQUIREMENTS
        response_data = EXAMPLE_SOURCE_DATA
        entity_stubs = EXAMPLE_ENTITY_DEFINITION
        schemas = {'Person': EXAMPLE_SCHEMA}
        submission_data, entities = utils.extract_entities(
            requirements,
            response_data,
            entity_stubs,
            schemas,
        )
        expected_entity = EXAMPLE_ENTITY
        self.assertEquals(
            len(expected_entity['Person']), len(entities['Person']))

    def test_extract_create_entities__no_requirements(self):
        '''
        If the mapping contains neither paths nor entity references, no
        entities can be extracted.
        '''
        submission_payload = EXAMPLE_SOURCE_DATA
        mapping_definition = {'mapping': [], 'entities': {}}
        schemas = {}
        submission_data, entities = utils.extract_create_entities(
            submission_payload,
            mapping_definition,
            schemas,
        )
        submission_errors = submission_data['aether_errors']
        self.assertEquals(len(submission_errors), 0)
        self.assertEquals(len(entities), 0)

    def test_extract_create_entities__success(self):
        '''
        Assert that no errors are accumulated and that the
        extracted entities are of the expected type.
        '''
        submission_payload = EXAMPLE_SOURCE_DATA
        mapping_definition = EXAMPLE_MAPPING
        schemas = {'Person': EXAMPLE_SCHEMA}
        submission_data, entities = utils.extract_create_entities(
            submission_payload,
            mapping_definition,
            schemas,
        )
        submission_errors = submission_data['aether_errors']
        self.assertEquals(len(submission_errors), 0)
        self.assertTrue(len(entities) > 0)
        for entity in entities:
            self.assertIn(entity.projectschema_name, schemas.keys())
            self.assertEquals(entity.status, 'Publishable')

    def test_extract_create_entities__validation_error(self):
        '''
        Assert that validation errors are accumulated and that they contain
        information about the non-validating entities.
        '''
        submission_payload = EXAMPLE_SOURCE_DATA
        mapping_definition = EXAMPLE_MAPPING
        # This schema shares the field names `id` and `name` with
        # EXAMPLE_SCHEMA. The field types differ though, so we should expect a
        # validation error to occur during entity extraction.
        error_count = 2
        schema = {
            'type': 'record',
            'name': 'Test',
            'fields': [
                {
                    'name': 'id',
                    'type': 'int',  # error 1
                },
                {
                    'name': 'name',  # error 2
                    'type': {
                        'type': 'enum',
                        'name': 'Name',
                        'symbols': ['John', 'Jane'],
                    }
                },
            ]
        }
        schemas = {'Person': schema}
        submission_data, entities = utils.extract_create_entities(
            submission_payload,
            mapping_definition,
            schemas,
        )
        submission_errors = submission_data['aether_errors']
        self.assertEquals(
            len(submission_errors),
            len(EXAMPLE_SOURCE_DATA['data']['people']) * error_count,
        )
        self.assertEquals(len(entities), 0)

    def test_extract_create_entities__error_not_a_uuid(self):
        submission_payload = {'id': 'not-a-uuid', 'a': 1}
        mapping_definition = {
            'entities': {'Test': str(uuid.uuid4())},
            'mapping': [
                ['$.id', 'Test.id'],
                ['$.a', 'Test.b'],
            ],
        }
        schema = {
            'type': 'record',
            'name': 'Test',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string',
                },
                {
                    'name': 'b',
                    'type': 'int',
                },
            ],
        }
        schemas = {'Test': schema}
        submission_data, entities = utils.extract_create_entities(
            submission_payload,
            mapping_definition,
            schemas,
        )
        submission_errors = submission_data['aether_errors']
        self.assertEqual(len(entities), 0)
        self.assertEqual(len(submission_errors), 1)
        self.assertIn('is not a valid uuid',
                      submission_errors[0]['description'])

    def test_is_not_custom_jsonpath(self):
        # Examples taken from https://github.com/json-path/JsonPath#path-examples
        example_paths = [
            '$.store.book[*].author',
            '$..author',
            '$.store.*',
            '$.store..price',
            '$..book[2]',
            '$..book[-2]',
            '$..book[0,1]',
            '$..book[:2]',
            '$..book[1:2]',
            '$..book[-2:]',
            '$..book[2:]',
            '$..book[?(@.isbn)]',
            '$.store.book[?(@.price < 10)]',
            '$..book[?(@.price <= $["expensive"])]'
            '$..book[?(@.author =~ /.*REES/i)]'
            '$..*',
            '$..book.length()',
        ]
        for path in example_paths:
            result = utils.custom_jsonpath_wildcard_regex.match(path)
            self.assertIsNone(result)

    def test_find_by_jsonpath__filter_by_prefix(self):
        obj = {
            'dose-1': {
                'id': 1,
            },
            'dose-2': {
                'id': 2,
            },
            'person-1': {
                'id': 3,
            },
        }
        expected = set([1, 2])
        path = '$.dose-*.id'
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)

    def test_find_by_jsonpath__filter_by_prefix_nested_base(self):
        obj = {
            'data': {
                'dose-1': {
                    'id': 1,
                },
                'dose-2': {
                    'id': 2,
                },
                'person-1': {
                    'id': 3,
                },
            }
        }
        expected = set([1, 2])
        path = '$.data.dose-*.id'
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)

    def test_find_by_jsonpath__nested(self):
        obj = {
            'dose-1': {
                'id': 1,
            },
            'dose-2': {
                'id': 2,
            },
            'person-1': {
                'id': 3,
                'household': {
                    'id': 4,
                },
            },
        }
        expected = set([4])
        path = '$.person-*.household.id'
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)

    def test_find_by_jsonpath__fallback_to_jsonpath_ng(self):
        obj = {
            'dose-1': {
                'id': 1,
            },
            'dose-2': {
                'id': 2,
            },
            'person-1': {
                'id': 3,
            },
        }
        expected = set([1, 2, 3])
        path = '$.*.id'
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)

    def test_find_by_jsonpath__fallback_array(self):
        obj = {
            'households': [
                {
                    'id': 1,
                },
                {
                    'id': 2,
                },
                {
                    'id': 3,
                },
            ]
        }
        expected = set([1, 2, 3])
        path = '$.households[*].id'
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)

    def test_validate_payload__success(self):
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
        result = utils.validate_payload(
            schema_definition=schema_definition,
            payload=payload,
        )
        self.assertTrue(result)

    def test_validate_payload__error(self):
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
            with self.assertRaises(utils.EntityValidationError) as err:
                utils.validate_payload(
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
        result = utils.validate_entities(entities=entities, schemas=schemas)
        self.assertEquals(len(result.validation_errors), len(entity_list) * 2)
